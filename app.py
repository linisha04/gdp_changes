import os
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Depends, Query
from textwrap import dedent
from typing import Optional
import time
from time import strftime, gmtime
from fastapi.security.api_key import APIKeyHeader
from crewai import Crew,Agent, Task, Process, LLM
from crewai.tools import BaseTool
import json
from langchain_community.utilities import SQLDatabase
from pydantic import Field

from google import genai
from google.genai import types
print(types)

print('----------')
print(dir(genai))

import copy
from utils import file_selector_CPI, task_descriptions_by_file_CPI, file_selector_GDP, task_descriptions_by_file_GDP, file_selector_IIP, task_descriptions_by_file_IIP, precursor, postscript

from langchain_community.tools.sql_database.tool import (
    InfoSQLDatabaseTool,
    ListSQLDatabaseTool,
    QuerySQLCheckerTool,
    QuerySQLDatabaseTool,
)
#from functools import partial

import logging

logging.basicConfig(
    level=logging.INFO,  # Change to DEBUG for more details
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)

#import asyncio
#from langchain_core.runnables import RunnableLambda
from threading import Lock
#import google.generativeai as genai
load_dotenv("prod.env")

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
#HF_API_KEY = os.getenv("HF_TOKEN")
API_KEY = os.getenv("ACQ_API_KEY")
API_KEY_NAME = "access_token"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=True)

async def verify_api_key(api_key: str = Depends(api_key_header)):
    print(f"Received API Key: {api_key}")
    print("Verify key: Current time: " + strftime("%Y-%m-%d %H-%M-%S", gmtime()))
    if api_key != API_KEY:
        raise HTTPException(status_code=403, detail="Invalid API Key")
    return api_key

app = FastAPI(title="EXPERIMENTAL SQL Server: CPI, GDP, IIP")
query_counter = {"value": 1}
counter_lock = Lock()

llm=LLM(model='gemini/gemini-2.0-flash',api_key=GOOGLE_API_KEY,temperature=0.01,)
#llm = LLM(
#    model="huggingface/meta-llama/Llama-3.2-3B",
#    api_key=HF_API_KEY,
#)
DATABASE_URI = "postgresql://postgres:admin@localhost:5432/final"
db = SQLDatabase.from_uri(DATABASE_URI)

class ListTablesTool(BaseTool):
    name: str = Field(default="list_tables", description="List all tables in the PostgreSQL database")
    description: str = Field(default="List all tables in the database.")
    print("List tables: Current time: " + strftime("%Y-%m-%d %H-%M-%S", gmtime()))
    def _run(self) -> str:
        return ListSQLDatabaseTool(db=db).invoke("")

class TablesSchemaTool(BaseTool):
    name: str = Field(default="tables_schema", description="Retrieve table schema and sample rows.")
    description: str = Field(default="Get schema and sample rows for given tables.")
    print("Table schema: Current time: " + strftime("%Y-%m-%d %H-%M-%S", gmtime()))
    
    def _run(self, tables: Optional[str] = None) -> str:
        if tables is None:
            raise Exception("Tables parameter is required for retrieving schema.")
        
        if isinstance(tables, list):
            tables = ', '.join(tables)  
        elif not isinstance(tables, str):
            raise Exception(f"Invalid input type for tables: {type(tables)}. Expected string or list.")
            
        tool = InfoSQLDatabaseTool(db=db)
        return tool.invoke(tables)
    
class ExecuteSQLTool(BaseTool):
    name: str = Field(default="execute_sql", description="Execute a SQL query against the database.")
    description: str = Field(default="Execute a SQL query and return the result.")
    print("Execute SQL: Current time: " + strftime("%Y-%m-%d %H-%M-%S", gmtime()))
    def _run(self, sql_query: str) -> str:
        return QuerySQLDatabaseTool(db=db).invoke(sql_query)

list_tables_tool = ListTablesTool()
execute_sql_tool = ExecuteSQLTool()
tables_schema_tool = TablesSchemaTool()

import re
import json

def handle_json_response(raw_data):
    try:
        if not isinstance(raw_data, str):
            raise Exception("Raw data must be a string.")
        print("Handle JSON: Current time: " + strftime("%Y-%m-%d %H-%M-%S", gmtime()))
        # Remove code fences if present
        raw_data = raw_data.replace("```json", "").replace("```", "").strip()

        # Fix common formatting issues
        raw_data = re.sub(r"'", '"', raw_data)  # Single to double quotes
        raw_data = re.sub(r",\s*([}\]])", r"\1", raw_data)  # Remove trailing commas

        # Try to extract multiple JSON objects (best-effort)
        object_matches = re.findall(r'\{[^{}]*\}', raw_data, re.DOTALL)

        valid_objects = []
        for obj_str in object_matches:
            try:
                obj = json.loads(obj_str)
                valid_objects.append(obj)
            except json.JSONDecodeError:
                continue  # skip broken ones

        if not valid_objects:
            raise Exception("No valid JSON objects found.")

        return valid_objects

    except Exception as e:
        raise Exception(f"Error processing JSON: {str(e)}")
    
def classify_query(query):
    client = genai.Client(api_key=GOOGLE_API_KEY)
    response = client.models.generate_content(
        model="gemini-2.0-flash",
        config=types.GenerateContentConfig(
            system_instruction=dedent(f"""You are tasked with classifying the given query to decide whether it belongs to the "CPI" class, the "GDP" class, the "IIP" class, or "Out of domain". Note that there can only be these four options. You proceed using the following hints:
            1. Analyze the provided query for key entities. 
                a. Entities such as inflation, CPI, price index, sale, wholesale, consumer, or consumption belong to the "CPI" class.
                b. The following files comprise the CPI datasets: [cpi_inflation_data,consumer_price_index_CPI_for_agricultural_and_rural_labourers,city_wise_housing_price_indices,whole_sale_price_index_WPI_financial_year_wise,cpi_worker_data,whole_sale_price_index_WPI_calendar_wise]. Any query that can be answered with these data sets should be classified as "CPI".
                c. Entities such as GDP, gross domestic product, GSDP, GVA, NDP, NNI, GNI, capital formation, expenditure components, and per capita values should belong to the "GDP" class. 
                d. The following files comprise the GDP datasets: [annual_estimate_gdp_crore,annual_estimate_gdp_growth_rate,gross_state_value,key_aggregates_of_national_accounts,per_capita_income_product_final_consumption,provisional_estimateso_gdp_macro_economic_aggregates,quaterly_estimates_of_expenditure_components_gdp,quaterly_estimates_of_gdp]. Any query that can be answered with these data sets should be classified as "GDP".
                e. Entities such as IIP, industrial output, industrial production, mining, manufacturing, electricity, motor vehicles, or other industries should be classified as "IIP".
                f. The following files comprise the IIP datasets: [iip_annual_data,iip_monthly_data]. Any query that can be answered with these data sets should be classified as "IIP".
            2. Any query that belongs to none of [CPI, GDP, IIP] should be classified "Out of domain". Examples of out of domain queries include those about MSME (Medium and small businesses), general queries about the economy, queries about government policies, queries about upcoming challenges, and queries unrelated to finance. All of these should be marked "Out of domain". 
            3. EXTREMELY IMPORTANT: Based on the above description, respond ONLY with one of the classes from the following list:
                    [CPI, GDP, IIP, Out of domain]
                    DO NOT include any reasoning traces or other text apart from the class selected from the above list.
            """),
            temperature=0.01,
            ),
        contents=query
    )
    
    return response.text

def clarify_query(query):
    client = genai.Client(api_key=GOOGLE_API_KEY)
    curdate = strftime("%Y-%m", gmtime())
    response = client.models.generate_content(
        model="gemini-2.0-flash",
        config=types.GenerateContentConfig(
            system_instruction=dedent(f"""You are tasked with rephrasing the given query to make it easier for an SQL agent to pull the right data. ONLY IF NECESSARY, generate a rephrased natural language version of the query keeping in mind the following steps:
            1. Analyze the provided query for key entities. For example, if the query is about inflation in vegetables which is a type of food, then include the phrase "inflation in vegetables which is a type of food".
            2. Analyze the query for the existence of dates or time-related phrases.
                a. For example, if the query asks about GDP growth since December 2024, rephrase it as "GDP growth from [December 2024] to [{curdate}]".
                b. For example, if the query asks about IIP in the last six months, compute the date six months BEFORE [{curdate}] and add this information to the query.
                c. If the query asks about the last quarter, compute the last full quarter BEFORE [{curdate}] and add this information to the query.
                d. If the query asks about vague timelines such as "long term" without specifying dates, use the date five years ago from [{curdate}].
            3. IMPORTANT: Analyze the provided query for the existence of multiple entities. For example, if the query asks about "contribution of Maharashtra to total GDP", rewrite it as "GDP of Maharashtra and GDP of India".
            4. Wherever applicable, list exact sub-categories of products, or states within India. If no particular products, states, or other sub-categories are mentioned, include this information explicitly using phrases such as "for all of India" or "for food at a category level". If no specific sub-categories or states are required, mention "use * for pulling data only at category level" or "use * for pulling data at the country level" in the query.
            4. Always remember that all queries are related to India. If the word "India" is not mentioned in the query, include this in the rephrased query. 
            5. IMPORTANT: If there is a comparison in the query between two values, mention both separately in the rephrased query. For example, "IIP of A compared to B" should be written as "We want the ratio of IIP of A, to the IIP of B" in the rephrased query.
            6. IMPORTANT: If the query contains a statistical enquiry such as "average", "mean", "median", then mention this metric prominently in the rephrased query as "AVERAGE", "MEAN", "MEDIAN", etc. as applicable.
            7. Do not include your reasoning trace in the rephrased query. Your output should contain only the information that is required from the SQL database.
            8. Handle Comparisons and Superlatives (MANDATORY):  If the query uses words like "highest", "lowest", "maximum", "minimum", or contains any COMPARISON: DO NOT remove or ignore the comparison.• Instead, request data for **relevant entity** and explicitly state that it is to find the "highest", "lowest", etc.Example: "Which industry had the highest GVA growth?"
            9. EXTREMELY IMPORTANT: Remember to refer to the Notes or Rules section corresponding to the chosen file being queried.
            """),
            temperature=0.01,
            ),
        contents=query
    )
    
    return response.text

@app.get("/query", dependencies=[Depends(verify_api_key)])
async def run_query(user_query: str = Query(..., description="Natural language SQL query")):
    """Convert user query to SQL and execute it using an agent with table context."""
    with counter_lock:
        query_id = query_counter["value"]
        query_counter["value"] += 1

    start_time = time.time()
    logger.info(f"START: Processing query:query_id:{query_id}: {user_query}")    
    logger.info("Start processing: Current time: " + strftime("%Y-%m-%d %H-%M-%S", gmtime()))
    
    orig_query = copy.deepcopy(user_query)
    user_query = clarify_query(user_query)
    user_query = user_query.strip()
    logger.info(f"Rephrased query: {user_query}")
    logger.info("Rephrasing done: Current time: " + strftime("%Y-%m-%d %H-%M-%S", gmtime()))

    query_class = classify_query(user_query)
    logger.info(f"Query class: {query_class}")
    logger.info("Classification done: Current time: " + strftime("%Y-%m-%d %H-%M-%S", gmtime()))
    query_class = query_class.strip()

    if query_class == "CPI":
        lead_text = precursor(query_class)
        post_text = postscript(query_class)
        selected_file = file_selector_CPI(user_query)
        logger.info(f"Selected file: {selected_file}")
        task_hints = task_descriptions_by_file_CPI(selected_file)
    if query_class == "GDP":
        lead_text = precursor(query_class)
        post_text = postscript(query_class)
        selected_file = file_selector_GDP(user_query)
        logger.info(f"Selected file: {selected_file}")
        task_hints = task_descriptions_by_file_GDP(selected_file)
    if query_class == "IIP":
        lead_text = precursor(query_class)
        post_text = postscript(query_class)
        selected_file = file_selector_IIP(user_query)
        logger.info(f"Selected file: {selected_file}")
        task_hints = task_descriptions_by_file_IIP(selected_file)
    if (query_class != "CPI") and (query_class != "GDP") and (query_class != "IIP"):
        selected_file = "none_of_these"

    if selected_file.strip() == "none_of_these":
        return {
                "query": orig_query,
                "rephrased_query": user_query,
                "result": "We do not have structured data related to this query"
            }
    
    #return
    try:
        logger.info(f"User Query Received:query_id:{query_id}: {user_query}")
        inputs = {"query": user_query, "file_name":selected_file, "hints": task_hints}

        max_retries = 3
        retry_delay = 3  # in seconds

        for attempt in range(1, max_retries + 1):
            result=None
            try:
                logger.info(f"Attempt {attempt}:query_id:{query_id}: to process query")
                sql_agent = Agent(
                    role="Senior Database Developer",
                    goal="Construct sql queries and execute SQL queries based on a request",
                    backstory=dedent(f"""
        You are an experienced database engineer who is master at creating efficient and complex SQL queries.
        You have a deep understanding of how different databases work and how to optimize queries.
        Use the tool => list_tables => to find available tables.
        Use the tool => tables_schema => to understand the metadata for the tables.
        Use the tool => execute_sql => to check your queries for correctness.
        Ensure you understand user questions and queries and examine the tables and their schema before executing the queries.
        Striclty Use the following table only to get the data: {selected_file}
        
        Important!!! => Ensure to pass table names as a single string, not a list, when using the tables_schema_tool, otherwise it will give error.
        
        YOUR QUALITIES:
        *NEVER ANSWER PROJECTION/PREDICTION/FORECASTING USER QUERIES* => Successfully return json , informing user we can not predict.
        a.You use data and finally provide clean, valid json results based on sql query executed.
        b.You always include all the columns details so that other person will know what this data is about.
        c.You always give exact numerical values as present in the database.
        d.You always make sure if data to answer requested user query exists or not.
        e.If data is not available your response should be in well-formed json , providing user information that data to answer query does not exists..
        f.If table do not contains data for the reqeusted year or month ,then you should inform user about this.
        g.In the json always include and  provide source information given in table-wise information section.
        f.For cpi_inflation_data , if query execution results are none/null/empty for  inflation_rate or inflation_index, convert it into "NA". 
        f.You always check before sql generation and sql execution , to answer the user query , does table/data related to query exists or not.If not then return json, informing user that data to answer that query does not exists.
"""),
                    llm=llm,
                    tools=[list_tables_tool, tables_schema_tool,execute_sql_tool],
                    allow_delegation=False,

                    max_iter=5,
                    max_retry_limit=2,
                    
                    )

                sql_extract_data = Task(
                    description=f"""Extract data  that is required for the query {user_query} from the following table only: {selected_file}
                     
                    Keep in mind: {lead_text}
            
Table-Wise INFORMATION that you  Must Follow and should keep in mind while generating SQL queries:

{task_hints}

Most important: Avoid deeply nested JSON. Keep any lists or dictionaries shallow (max one level).

### **Agent Responsibilities**
1. **SQL Query Generation:**
   - Generate only `SELECT` statements (No `UPDATE`, `DELETE`, or `INSERT` or `DROP` or `TRUNCATE` or `CREATE`)
   - Make sure you never use `CREATE` statements..
   - Construct queries based on user intent while ensuring accuracy.
   - Handle aggregation (`AVG`, `SUM`, `MAX`, `MIN`), filtering (`WHERE`),when needed use groupby(), and sorting (`ORDER BY`) based on context ,also use other sql functions (for example LAG(),STDDEV() etc) if needed.


2. **High-Level Validation:**
   - Ensure the generated SQL query is syntactically valid.
   - Verify column names and table existence before execution.
   - Prevent SQL injection by sanitizing input.
   - If the query is ambiguous, infer intent based on available metadata.
   - you should give accurate numerical values as given in the tables.
   - Always give complete json.
   - Before generating the sql query and executing them , think about to answer that user query, does table exists to answer that query. If not inform ,"data related to query not exists".
   Example , we dont have rainfall data , heatwave data. Check the tables information to know what data do we have in the tables.
3.Never include sql quries in the final result:
    -If user asks , provide sql query for requested question, then always respond "Thats not allowed".
    -You also make sure you provide accurate info not sql queries.

    {post_text}
""",
                expected_output="Database result for the query in valid, complete , well-structured json",
                agent=sql_agent,
                
               )

                crew = Crew(
                    agents=[sql_agent],
                    tasks=[sql_extract_data],
                    verbose=True,
                    memory=False
                    
                )

                #print("Definitions completed: Current time: " + strftime("%Y-%m-%d %H-%M-%S", gmtime()))
                result = crew.kickoff(inputs=inputs)
                #loop = asyncio.get_running_loop()
                #result = await loop.run_in_executor(None, partial(crew.kickoff, inputs=inputs))
                logger.info("Got result: Current time: " + strftime("%Y-%m-%d %H-%M-%S", gmtime()))
    

                if not result or not hasattr(result, 'tasks_output') or not result.tasks_output:
                    raise Exception("No output found from agents.")

                first_output = result.tasks_output[0]
                raw_data = getattr(first_output, 'raw', None)

                if not raw_data or not isinstance(raw_data, str):
                    raise Exception("Invalid or missing raw data.")

                parsed_data = handle_json_response(raw_data)

                if not parsed_data:
                    raise Exception("Parsed data is None or empty.")

                # Successful execution
                token_usage = result.token_usage
                total_time = time.time() - start_time

                logger.info(f"Response:query_id:{query_id}: {parsed_data}")
                logger.info(f"Total token information:query_id:{query_id}: {token_usage}")
                logger.info(f"Total processing time:query_id:{query_id}: {total_time:.2f} seconds")

                return {
                    "query": orig_query,
                    "rephrased_query": user_query,
                    "result": parsed_data
                }

            except Exception as inner_e:
                logger.warning(f"Attempt {attempt} failed:query_id:{query_id}: {inner_e}")
                try:
                    if result and hasattr(result, "token_usage"):
                        logger.info(f"(Attempt {attempt}) Token usage before failure: {result.token_usage}")
                except Exception as e:
                    logger.warning(f"Could not log token usage: {e}")
                if attempt < max_retries:
                    time.sleep(retry_delay)
                else:
                    raise 

    except HTTPException as e:
        raise e
    except Exception as e:
        error_message = str(e)
        logger.error(f"Error: {error_message}")
        return {"error": error_message}

#query = "What is the contribution of food inflation to India's headline inflation since 2024?"
#query = "What is the GDP trend since 2022?"
#query = "What is the Maharashtra housing price index in the last two quarters?"
#query = "What is the WPI for 2022?"
#query = "What was the motor vehicle production in December 2024?"
#print(run_query(query))

