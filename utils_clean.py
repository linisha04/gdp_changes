import os
from textwrap import dedent
from time import strftime, gmtime
from google import genai
from google.genai import types
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

def precursor(datatype):
    datatype = datatype.strip()
    text_to_return = {
    "CPI": """
        Important side notes!!!!
        - Examine what user is aking ,
        -If query is about inflation index / cpi index for that , information is present in column inflation_index.
        -If query is about inflation rate or percentage for that ,  information is present in column inflation_rate.       
        -If in query no inflation rate/percentage or inflation index is mentioned , provide results for both.
        For example: What is the inflation of india for last 3 month:
                        Provide results including both inflation_rate and inflation_index for the latest three months.
            
        Some Important Notes:
        - Make sure numerical values are actual and correct as in the database and before executing the query make sure column names are always correct and make use of all the available tools.
        - Make sure information asked for year exists if not exists then  return a  response in the json telling user , data to answer that query dont exist
        - Maintain correct column names as per the schema.
        - Very Very Important!! : Always give complete full json, if reponse too long then make sure  that json is complete and well structured.
        - If no data is aviilable related to user query then inform user or ask for more context.
        - cpi_inflation_data  table contains data from year 2017to 2025 only, so if user query requires data for other years then you should inform user about this.
        - For whole sale price index(wpi) queries , always query Query whole_sale_price_index_WPI_financial_year_wise if user query does not specify calendar year or financial year.
        - In the final json ,if inflation_rate or inflation_index is empty or None or null , strictly convert it into "NA", instead of bluntly telling user "data is null in the database".
        -*In response ,json should be complete , well-structured , should have all the fields data in each json  , and the data_source should be present in every json .Data Source information is given in table-wise information.
        -You provide  sql execution result in well-structured complete json , along with "data_source" field .Do not interpret or summarize the result in final answer.        
        """,
    "GDP": """
        1. Some Important Notes:
        - Make sure numerical values are actual and correct as in the database and before executing the query make sure column names are always correct and make use of all the available tools.
        - Make sure information asked for year exists if not exists then  return a  response in the json telling user , data to answer that query dont exist
        - Maintain correct column names as per the schema.
        - Very Very Important!! : Always give complete full json, if reponse too long then make sure  that json is complete and well structured.
        - If no data is aviilable related to user query then inform user or ask for more context.
        - In response ,json should be complete , well-structured , should have all the fields data in each json  , and the data_source should be present in every json .Data Source information is given in table-wise information.
        -You provide  sql execution result in well-structured complete json , along with "data_source" field .Do not interpret or summarize the result in final answer.        

        2.Some general important rules:
        *Only "quaterly_estimates_of_expenditure_components_gdp" and "quaterly_estimates_of_gdp" have quater wise data for years , rest mentioned tables are having yearly data.
        A.If user asks gdp related data for month , successfully return the the requested data for year mentioned in the query or return latest year if year is not mentioned.And inform we have yearly data.
        B.In response ,json should be complete , well-structured , should have all the fields data in each json  , and the data source should be present in every json .Data Source information is given in table-wise information.
        C.You provide  sql execution reuslt in well-structured complete json form along with "data_source" field .Do not interpret or summarize the result in final answer of your.
        D.If we do not have data for the requested year , inform user about that in a message in well-structured  json , do not provide false values.

        3.Some full forms for reference:
        *GVA at basic prices = Gross Value Added at Basic Prices
        *GDP = Gross Domestic Product
        *GNI = Gross National Income
        *NNI = Net National Income
        *NDP = Net Domestic Product
        *CFC = Consumption of Fixed Capital 
        *PFCE = Private Final Consumption Expenditure
        *GFCE = Government Final Consumption Expenditure
        *GCF = Gross Capital Formation
        *GFCF = Gross Fixed Capital Formation
        *CIS = Change in Inventories (also known as "Change in Stocks")
        *GNDI = Gross National Disposable Income
        *NNDI = Net National Disposable Income
        *Gross Saving to GNDI = Ratio of gross saving to Gross National Disposable Income
        *GCF to GDP = Ratio of Gross Capital Formation to GDP
        *PFCE to NNI = Private Final Consumption Expenditure as a ratio to Net National Income

        4.Sectoral Breakdown
        *These are part of economic sectors contributing to GDP:
        Primary Sector , Agriculture, Livestock, Forestry & Fishing , Mining & Quarrying , Secondary Sector ,Manufacturing ,Electricity, Gas, Water Supply & Other Utility Services ,Construction ,Tertiary Sector ,Trade, Hotels, Transport, Communication & Services related to Broadcasting ,Financial, Real Estate & Professional Services ,Public Administration, Defence & Other Services
        *These are not "sectors" but high-level aggregates or economic indicators:
        GVA at Basic Prices , NVA at Basic Prices ,GNI (Gross National Income) , NNI (Net National Income) , Per capita income (Rs.), Net Taxes on Products ,GDP,GFCE (Government Final Consumption Expenditure),PFCE (Private Final Consumption Expenditure),GFCF (Gross Fixed Capital Formation),CIS (Change in Inventories/Stocks),Valuables, Exports of goods and services , Imports of goods and services , Discrepancies

        Based on Point 4, Check the intent of question, what query is asking.
        For example: Which industry had the highest GVA Growth Rate at constant prices in 2022-23 (First Advance Estimates)?" => you should give result for the highes sector. choose only sectors here not economic indicators
        What is the cumulative Gross Value Added at current prices for all industries in 2024-25 (Second Advance Estimates)? => choose only sectors here not economic indicators and provide cumulative Gross Value Added sum.

        NOTE: Deeply go through these table  information and form correct filtering conditions , match the strings correctly.
        You are retrieving economic data from structured tables. Each table includes clearly defined string values for columns.
        🔒 Always use **exact string matches** from the predefined value lists.
        Do not attempt to guess or modify terms. If a mismatch is likely, confirm with the user or suggest closest matches. This prevents incorrect SQL queries.
        And Do Not Round Off Any Numerical Values.Provide Exact Database Match.
        Check User is asking for economin sector information for gdp component information.
        For example: What is the GDP growth rate for q1 2024-25? at constant price, => Answer should be => 
        "year": "2024-25",
        "item": "GDP ",
        "quater": "Q1",
        "value": 4441986,
        "price_type": "constant price",
        "data_source": "MoSPI", until specifically asked for economic sector of gdp component.
        """,
    "IIP": """
        -Make sure numerical values are correct as present in the database.
        -If no data is aviilable related to user query then inform user or ask for more context and for data unavailability your response should be in this json format telling the user about data unavailability.
        -Use the designated table only, to get the data and ensure to pass table names as a single string, not a list, when using the tables_schema_tool.
        -Maintain correct column names as per the schema.
        -If the query is ambiguous , infer intent based on available metadata use tools for that.
        -If user query is non-factual and miss the year then you should use the latest year/month present in the database.
        -Refrain from querying whole table.
        -Important!! => Never form sql queries that invoves querying whole table.Query only the latest year present in the database,If no year present in the query.
        -Important!! => Before forming queries or executing , understand the user query and check , is query answerable or not or related to iip_annual_data or iip_monthly_data table or not . If not handle it properly and provide clear reponse in well-structured json.
                   
        A.Some general important rules:
        *In response ,json should be complete , well-structured , should have all the fields data in each json.
        *You provide  sql execution result in well-structured complete json.Do not interpret or summarize the result in final answer.
        *iip_annual_data => This table contains annual Index Of Industrial Production (IIP) data.
        *iip_monthly_data => This table contains monthly Index Of Industrial Production (IIP) data.
        *Make sure to execute the correct query based on whether the requested data pertains to a month or a year. 
        *If the year/month is not mentioned in the query, use the **latest available year or month** data from the respective table. Ensure to return the **exact numerical values** as they are stored in the database.And avoid rounding off any values in the final answer.
        *If iip_index ,iip_growth_rate results in None/empty replace it with "NA" in the final json.
        """,
    "MSME": """
        You are an experienced data engineer specializing in MSME-related data. Your expertise includes analyzing sector-wise MSME contributions,
        employment trends, investment patterns, GDP impact, and exchange rate influences.

        Use the following tools appropriately:
        - `list_tables`: To find available tables.
        - `tables_schema`: To understand table structures.
        - `execute_sql`: To run queries and retrieve results.

        Extract MSME-related data based on the user’s request.
        - Ensure that column names match exactly as per the schema.
        - Use appropriate filtering conditions to refine results.
        - Handle aggregations (`SUM`, `AVG`, `MAX`, `MIN`), filtering (`WHERE`), grouping (`GROUP BY`), and sorting (`ORDER BY`) based on user intent.
        - If data is unavailable, return ["status = Your Error description here"].
    """
    }
    return text_to_return[datatype]

def postscript(datatype):
    datatype = datatype.strip()
    text_to_return = {
    "CPI": """
        ### Rules for Query Generation:
        1. Generate and execute query only if user query is related to inflation rate , inflation index , whole sale price index(wpi) , consumer price index (cpi) , housig price index(hpi) , consumer price index for industrial or agriculture workers. If query is irrelevant inform user about that and ask for more context.
        2. Ensure queries are **optimized** and **structured correctly**.
        3. If the user asks for trends, perform **aggregations** or **time-series comparisons** as needed.
        4. If the user asks for a summary, **group data** by relevant fields.
        5. If the user asks for state-wise comparisons, include **GROUP BY state**.
        6. If the user asks for inflation-related queries, focus on **inflation_percentage**.
        7. If the user requests data for a specific period, use **year** and **month** to filter.
        """,
    "GDP": """
        =>Handling "year" column:
        a.Format of years columns are like this : "2023-24","2019-20","2011-12" etc.... 
        b.so when asked query for a year, for example 2023 you take it like 2023-24 always.
        c.Also make sure when error comes in years column you check the schema and few rows of the tables to know the format.
        d.Dont give id column of the tables in the json response.
        e.Always try navigate the unique values in the columns so that you choose the most relevant table and give correct result.
        f.Always check if the user query includes a specific year. If not, automatically use the latest current available year from the dataset.

        ### Rules for Query Generation:
        1. Ensure queries are **optimized** and **structured correctly**.
        2. If the user asks for trends, perform **aggregations** or **time-series comparisons** as needed.
        3. If the user asks for a summary, **group data** by relevant fields.
        4. If the user asks for state-wise comparisons, include **GROUP BY state**.
        6. If the user requests data for a specific period, use **year**  filter.
    """,
    "IIP": """
        Determine the context:

        Context: 
            a.sector_type='General' has category='General' and sub_category='*'. This means overall iip_index/iip_growth_rate.
            b.sector_type='Sectoral' has category=["Mining","Manufacturing","Electricity"] and sub_category='*' . This will give genral sectoral iip_index/iip_growth_rate.
                   If user query includes specific sub_category then ,for sector_type='Sectoral' specific sub_category are  =>["Manufacture of Furniture","Manufacture of Basic Metals","Manufacture of Electrical Equipment","Manufacture of Motor Vehicles, Trailers and Semi-trailers","Other Manufacturing","Manufacture of Machinery and Equipment N.e.c.","Manufacture of Computer, Electronic and Optical Products","Manufacture of Tobacco Products","Manufacture of Fabricated Metal Products, Except Machinery and Equipment","Manufacture of Chemicals and Chemical Products","*","Printing and Reproduction of Recorded Media","Manufacture of Wearing Apparel","Manufacture of Pharmaceuticals, Medicinal Chemical and Botanical Products","Manufacture of Other Transport Equipment","Manufacture of Textiles","Manufacture of Wood and Products of Wood and Cork, Except Furniture; Manufacture of Articles of Straw and Plaiting Materials","Manufacture of Beverages","Manufacture of Leather and Related Products","Manufacture of Food Products","Manufacture of Coke and Refined Petroleum Products","Manufacture of Rubber and Plastics Products","Manufacture of Paper and Paper Products","Manufacture of Other Non-metallic Mineral Products"]
            c.sector_type='Use-based category' has category => ["Primary Goods","Capital Goods","Intermediate Goods","Infrastructure/ Construction Goods","Consumer Durables"] and sub_category='*'
                  IF query includes ["Primary Goods","Capital Goods","Intermediate Goods","Infrastructure/ Construction Goods","Consumer Durables"]  then set sector_type='Use-based category' 

        -Is the user asking for General IIP, Sectoral data, or Use-Based classification? 
        e.g Which sector had highest IIP in 2024 for India?" 
            => sector_type='Sectoral' ,sub_category='*' ,here you have to for category having highest iip index. 
            => You have to answer for  these categories => ["Mining","Manufacturing","Electricity"]
            => Do not look at sub_category level.Hence sub_category='*'.
        e.g what is the iip in 2024 ? => sector_type='General' and sub_category='*' and category='General'
        e.g What is the iip for Capital Goods? sector_type='Use-based category' and  category='Capital Goods'

        Take help from table-wise information for setting where conditions.

        Formulate filter conditions based on the dataset:
        -sector_type, category, sub_category, and year and month should be correctly selected.
        -For general questions, set sub_category = '*'.
        -For specific sectors or use-based classifications, match sub_category exactly.
        -If the query contains terms like "overall", "total", or "general" , set: sub_category='*' and sector_type='General' , category='General'
        -If date or year or month is not specified, assume the latest available year or month from the dataset.
        -Keep sub_category='*' and  category='General' and sector_type='General' , until explicility asked.
        -IF query includes sectoral set : sector_type='Sectoral' and sub_category='*' 
        -YOU MUST SET sub_category='*'  IN SQL QUERIES UNTIL SPECIFIC sub_category IN THE QUERY IS MENTIONED

        ### Default Filter Logic (MOST IMPORTANT STEP) :
        If the user does not specify `category`, `subcategory`, or `sector_type`, then apply the following defaults in the WHERE clause:
        - category = 'General'
        - subcategory = '*'
        - sector_type = 'General'
        These must be included in all queries unless the user overrides them.

        D.Use These Examples To Answer General Queries
        Examples:
        a.what is the IIP for last 6 months?  => keep sector_type='General' , category='General' , sub_category='*' , do group by month, 
        b.what is the iip index for manufacturing sector => WHERE category = 'Manufacturing' AND subcategory = 'General' AND type = 'General' 
        c.Which sector has the highest IIP index? => Where sub_category = '*' AND sector_type = 'Sectoral'
            
        Some rules that you should follow:
        1. **ENSURE ALL SELECT STATEMENTS INCLUDE THE All THE RELEVANT  FIELDS:**  
        - Queries **must be fully structured and accurate**.  

        2. **DEFAULT CONDITIONS (UNTIL SPECIFIED OTHERWISE IN THE QUESTION):**  
        - If no specific year is mentioned in the user query then year should be the latest year present in the database.
        
        ### **Agent Responsibilities**
        1. **SQL Query Generation:**
        - Generate only `SELECT` statements (No `UPDATE`, `DELETE`, or `INSERT` or `DROP` or `TRUNCATE` or `CREATE`).
        - Construct queries based on user intent while ensuring accuracy.
        - Handle aggregation (`AVG`, `SUM`, `MAX`, `MIN`), filtering (`WHERE`),when needed use groupby(), and sorting (`ORDER BY`) based on context ,also use other sql functions (for example LAG(),STDDEV() etc) if needed.

        2. **High-Level Validation:**
        - Ensure the generated SQL query is syntactically valid.
        - Verify column names and table existence before execution.
        - Prevent SQL injection by sanitizing input.
        - If the query is ambiguous, infer intent based on available metadata use tools for that.

        ### Rules for Query Generation:
        1. Always SELECT all columns unless specified.
        2. If the user asks for trends, perform **aggregations** or **time-series comparisons** as needed.
        3. If the user asks for a summary, **group data** by relevant fields.
        4. Prioritize **filter accuracy**: if the user mentions any timeframe (e.g., "2022", "last 3 months", "Feb 2024"), use `year` and/or `month` filters accordingly.
        5. If the user asks for inflation-related queries, focus on **inflation_percentage**.
        6. If the user requests data for a specific period, use **year** **month** filter.
    """,
    "MSME": """
        - If the requested year is missing, assume the latest available year.
        - Ensure accurate numerical values in the response.
        - Understand the difference between state and country for correct table reading.
        - In `state_wise_udyam_registration_sheet0` Always exclude the row where "state/ut_name" = 'Total' in your queries. Use it only when the user asks for aggregate , total data across all states/UTs.
        - Ensure queries are **optimized** and **structured correctly**.
        - If the user asks for trends, perform **aggregations** or **time-series comparisons** as needed.
        - If the user asks for months data use the date column .
   
        ### **Agent Responsibilities**
        1. **SQL Query Generation:**
        - Generate only `SELECT` statements (No `UPDATE`, `DELETE`, or `INSERT` or `DROP` or `TRUNCATE` or `CREATE`)
        - Make sure you never use `CREATE` statements..
        - Construct queries based on user intent while ensuring accuracy.
        - Handle aggregation (`AVG`, `SUM`, `MAX`, `MIN`), filtering (`WHERE`),when needed use groupby(), and sorting (`ORDER BY`) based on context ,also use other sql functions (for example LAG(),STDDEV() etc) if>
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
        
        **Foreign Key Relationships / Inferred Connections:**
        - **Country:** The `country` column appears in many tables (`cleaned_adb_asia_sme`, `exchange_rate_lcy_usd`, `gdp_(current_prices)`, and tables `a1` through `a14`). This is the most obvious and important link between tables, allowing you to analyze MSME data in relation to country-level economic indicators.
        - **Sector:** The `sector` column appears in `bdi(1)`, `cleaned_adb_asia_sme`, `a3._msmes_by_sector`, `a7._msme_employees_by_sector`, This allows for the analysis of MSME performance by sector.

        **Suggested Join Keys/Logic:**
        - To analyze MSME numbers, GDP contribution, and export performance for a specific country over time, you would join tables `a1._number_of_msmes`, `a10._msme_contribution_to_gdp`,  `a13_2._msme_export_value_(million)`, etc., on the `country` column. You'll need to handle the `text` data types of the year columns and convert them to numeric for analysis.
        - To get the MSME definitions used for a particular country, join the tables such as `a1._number_of_msmes` with `cleaned_adb_asia_sme` on the `country` column.
        - To incorporate exchange rates into the analysis, join the MSME tables with `exchange_rate_lcy_usd` on the `country` column.  This is crucial for converting local currency values to USD for cross-country comparisons.
        - To understand the context of MSME sector GDP contribution from  `a11._msme_gdp_by_sector` with the overall GDP `gdp_(current_prices)`

        **Example Queries:**
        - "What was the total MSME employment in Maharashtra in 2023?"
        - "Compare MSME investment trends in the manufacturing and service sectors for the past five years."
        - "Show the top 5 states with the highest MSME contribution to GDP in 2022."
        - "What is the average employment per MSME unit across all states?" 

        The agent should ensure structured and optimized SQL queries, verifying their correctness before execution.
    """
    }
    return text_to_return[datatype]

def file_selector_CPI(query):
    client = genai.Client(api_key=GOOGLE_API_KEY)
    curdate = strftime("%Y-%m", gmtime())
    response = client.models.generate_content(
        model="gemini-2.0-flash",
        config=types.GenerateContentConfig(
            system_instruction=dedent(f"""you are tasked with identifying the file which contains required data, based on the query: {query}.
                    you must pick one file name only from the following list:
                    1. cpi_inflation_data: this table covers data for year 2017 to 2025. if in doubt, all queries related to inflation and consumer price index should go here.
                    2. consumer_price_index_cpi_for_agricultural_and_rural_labourers: this table covers data for year 2024. it should be used only when "agriculture labour" or "rural labour" is mentioned. DO NOT use this file unless "labour" is specifically mentioned.
                    3. city_wise_housing_price_indices: this table covers data for year 2014 to 2024. it should be used only when housing prices are mentioned.
                    4. whole_sale_price_index_wpi_financial_year_wise: this table covers data for year 2012 to 2023. it should be used only when wpi or wholesale prices are mentioned in financial year or fy format.
                    5. cpi_worker_data: this table covers data for year 2011 to 2023. it should be used only when workers are mentioned. examples are rural workers, factory workers.
                    6. whole_sale_price_index_wpi_calendar_wise: this table covers data for year 2013 to 2023. it should be used only when wpi or wholesale prices are mentioned in calendar year format.
                    7. none_of_these: for any queries which are unrelated to inflation. for example, queries regarding gdp, iip, msme would fall under the "none" category. queries regarding the general state of the economy, government policies, and upcoming challenges also fall under the none_of_these category.
                    
                    ## Consider the list above, and respond ONLY with one of the file names from the following list:
                    [cpi_inflation_data,consumer_price_index_cpi_for_agricultural_and_rural_labourers,city_wise_housing_price_indices,whole_sale_price_index_wpi_financial_year_wise,cpi_worker_data,whole_sale_price_index_wpi_calendar_wise,none_of_these]
                    do not include any reasoning traces or other text apart from the file name selected from the above list.
            """),
            temperature=0.01,
            ),
        contents=query
    )
    
    return response.text

def file_selector_GDP(query):
    client = genai.Client(api_key=GOOGLE_API_KEY)
    curdate = strftime("%Y-%m", gmtime())
    response = client.models.generate_content(
        model="gemini-2.0-flash",
        config=types.GenerateContentConfig(
            system_instruction=dedent(f"""You are tasked with identifying the file which contains required data, based on the query: {query}.
                    You MUST pick one file name ONLY from the following list:
                    For indentifying understand the table names and what sectors/components these tables convers.
                    You MUST pick one file name ONLY from the following list:
                    Go through entire list and key-words then select the most relevant table.
                    1. annual_estimate_gdp_crore: Use this table when the query asks for the actual GDP value (in ₹ crores).(i.e If the query is about “how much” a sector or economic indicator contributed to GDP (in ₹ crores) — use this table.).These component/sector includes ["Trade, Hotels, Transport, Communication & Services related to Broadcasting","Net taxes on Products  ","Manufacturing","Construction","Net taxes on Products","PFCE","Public Administration, Defence & Other Services","GFCE","Tertiary Sector","GVA at Basic Prices","Imports of goods and services ","GNI  ","CIS","NNI ","Financial, Real Estate & Professional Services","Mining & Quarrying","Discrepancies ","Secondary Sector","NVA at Basic Prices","Agriculture, Livestock, Forestry & Fishing","GFCF","GNI ","Exports of goods and services","Electricity, Gas, Water Supply & Other Utility Services","Imports of goods and services","Valuables","GDP ","Per capita income(Rs.)","Primary Sector"]
                    2. annual_estimate_gdp_growth_rate:   Use this table when your question is about how fast or slow a sector/component is growing. It contains percentage growth rates instead of actual GDP values. These Component/sector includes  ["Trade, Hotels, Transport, Communication & Services related to Broadcasting","Agriculture, Livestock, Forestry & Fishing","Manufacturing","GFCF","Construction","3.3 Public Administration, Defence & Other Services","GNI ","Net taxes on Products","Public Administration, Defence & Other Services","PFCE","GFCE","Tertiary Sector","Exports of goods and services","GVA at Basic Prices","Electricity, Gas, Water Supply & Other Utility Services","CIS","Imports of goods and services","Valuables","GDP ","NNI ","Financial, Real Estate & Professional Services","Mining & Quarrying","Discrepancies ","Per capita income(Rs.)","Secondary Sector","NVA at Basic Prices","Primary Sector"]
                    3. gross_state_value: Use this table when the query is about state-level economic performance — specifically when it refers to the value generated by sectors within individual states (GVA) or asks for Gross State Domestic Product (GSDP).These Component/sector includes  ["Electricity, gas, water supply & other utility services","Fishing and aquaculture","Storage","Manufacturing","Financial services","Construction","Trade, repair, hotels and restaurants","Tertiary","Road transport#","Population","Livestock","Agriculture, forestry and fishing","Air transport","Road transport","Primary","Transport, storage, communication & services related to broadcasting","Road transport*","Trade & repair services**","Other services","Water transport","Per Capita GSDP","TOTAL GSVA at basic prices","Taxes on Products#","Railways","Public administration","Trade & repair services ","Crops","Communication & services related to broadcasting","Real estate, ownership of dwelling & professional services","Taxes on Products","Mining and quarrying","Gross State Domestic Product","Trade & repair services","Services incidental to transport","Secondary","Subsidies on products","Forestry and logging","Hotels &  restaurants",]
                    4. key_aggregates_of_national_accounts: Use this table if the query is about macroeconomic indicators (savings, income, consumption, capital formation, ROW transfers) at the national level .These are ["Gross Saving","GVA at basic prices","Less Imports of goods and services","Import of goods","Less Subsidies on Products","GDP","Export of goods","PFCE","GFCE","Primary income receivable from ROW (net)","Import of services","CIS","GNI","Export of services","Export of goods and services","GNDI","Taxes on Products including import duties","CFC","VALUABLES","GCF","Net Saving","NNDI","Rates","GFCF","Less Import of goods and services","GCF  excluding Valuables to GDP","Other current transfers (net) from ROW","GCF to GDP","Gross Saving to GNDI","NNI","PFCE to NNI","Exports of goods and services","NDP","Valuables","Discrepancies"]
                    5. per_capita_income_product_final_consumption:This table contains per capita estimates of key economic indicators in ₹ (Indian Rupees) or growth rate (%) for various years, along with the population used for those calculations. The indicators relate to income and consumption at both current and constant prices.these measures are ["Per Capita GDP","Per Capita GNI","Per Capita NNI","Per Capita GNDI","Per Capita PFCE"]
                    6. provisional_estimateso_gdp_macro_economic_aggregates: This table contains provisional estimates of major macroeconomic aggregates like GDP, GVA, NDP, NNI, GNI, capital formation, expenditure components, and per capita values for the most recent years. These are ["Change in stocks","Change in Stocks","Government Final Consumption Expenditure","Gross Fixed Capital Formation","Gross National Income (GNI)","Per capita NNI","Less Imports","Exports","Private Final Consumption Expenditure","Gross fixed capital formation","Private final consumption expenditure","Gross Domestic Product (GDP)","Discrepancies","Valuables","Net Domestic Product (NDP)","Net National Income (NNI)","Government final consumption expenditure","Gross Value Added (GVA) at basic prices","Per Capita NNI"]
                    7. quaterly_estimates_of_expenditure_components_gdp: This table gives quarter-wise estimates of expenditure components of GDP for multiple years, at both:Current Prices (nominal, without inflation adjustment),Constant Prices (real, inflation-adjusted).It includes major components like:Private/Government Final Consumption Expenditure,Gross Fixed Capital Formation,Imports & Exports of goods/services,Change in stocks,Discrepancies,Valuables,GDP.  These components are ["Private final consumption expenditure","Gross fixed capital formation","Change in stock","Discrepancies","Valuables","Gross domestic product","Government final consumption expenditure","Less: Imports of goods and services","Exports of goods and services"]
                    8. quaterly_estimates_of_gdp: This table provides quarterly  performance estimates/growth_value of  sectors and GDP components, such as: Agriculture, Manufacturing, Services, etc.Growth rates for these sectors during each quarter.These components are ["Trade, Hotels, Transport, Communication & Services related to Broadcasting","Agriculture, Livestock, Forestry & Fishing","Manufacturing","GFCF","Construction","PFCE","Public Administration, Defence & Other Services","GFCE","Tertiary Sector","Exports of goods and services","GVA at Basic Prices","Electricity, Gas, Water Supply & Other Utility Services","CIS","Imports of goods and services","Valuables","GDP ","Financial, Real Estate & Professional Services","Mining & Quarrying","Discrepancies* ","Secondary Sector","Primary Sector"].
                                      
                    ## Consider the list above, and respond ONLY with one of the file names from the following list:
                    [annual_estimate_gdp_crore,annual_estimate_gdp_growth_rate,gross_state_value,key_aggregates_of_national_accounts,per_capita_income_product_final_consumption,provisional_estimateso_gdp_macro_economic_aggregates,quaterly_estimates_of_expenditure_components_gdp,quaterly_estimates_of_gdp,none_of_these]
                    DO NOT include any reasoning traces or other text apart from the file name selected from the above list.
            """),
            temperature=0.01,
            ),
        contents=query
    ) 
    
    return response.text

def file_selector_IIP(query):
    client = genai.Client(api_key=GOOGLE_API_KEY)
    curdate = strftime("%Y-%m", gmtime())
    response = client.models.generate_content(
        model="gemini-2.0-flash",
        config=types.GenerateContentConfig(
            system_instruction=dedent(f"""You are tasked with identifying the file which contains required data, based on the query: {query}.
                    You MUST pick one file name ONLY from the following list:
                    1. iip_annual_data: This file contains Index of Industrial Production data on an annual or yearly basis.
                    2. iip_monthly_data: This file contains Index of Industrial Production data on a monthly basis. Use this file only if the query mentions the word monthly or if it specifies certain months.
                    Consider the list above, and respond ONLY with one of the file names from the following list:
                    [iip_annual_data,iip_monthly_data,none_of_these]
                    DO NOT include any reasoning traces or other text apart from the file name selected from the above list.
            """),
            temperature=0.01,
            ),
        contents=query
    )
    
    return response.text

def file_selector_MSME(query):
    client = genai.Client(api_key=GOOGLE_API_KEY)
    curdate = strftime("%Y-%m", gmtime())
    response = client.models.generate_content(
        model="gemini-2.0-flash",
        config=types.GenerateContentConfig(
            system_instruction=dedent(f"""You are tasked with identifying the file which contains required data, based on the query: {query}.
        You MUST pick one file name ONLY from the following list:
        1. Use `bdi(1)` for credit growth analysis. "columns": ["year", "month", "sector", "growth_rate_yoy", "previous_year_growth", "remarks"]
        2. Use `cleaned_adb_asia_sme` for international MSME comparisons. "columns": ["sector","criteria","micro_threshold","small_threshold","medium_threshold","country"]
        3. Use `exchange_rate_lcy_usd` for currency exchange rate analysis. "columns": ["country","2003","2004","2005","2006","2007","2008","2009","2010","2011","2012","2013","2014","2015","2016","2017","2018","2019","2020","2021","2022"]
        4. Use `gdp_(current_prices)` for GDP trends. "columns": ["country","2003","2004","2005","2006","2007","2008","2009","2010","2011","2012","2013","2014","2015","2016","2017","2018","2019","2020","2021","2022"]
        5. Use `state_wise_udyam_registration` for MSME , Udyam registrations and micro ,small , medium sector registeration by state.  "columns": ["s__no_", "state/t_name", "total_msmes","total_udyam","imes_(uap)","micro","small","medium"]
        6. Use 'a2._msmes_to_total' for the percentage of MSMEs among all enterprises by country . "columns": ["country","2003","2004","2005","2006","2007","2008","2009","2010","2011","2012","2013","2014","2015","2016","2017","2018","2019","2020","2021","2022"]
        7. Use 'a3._msmes_by_sector' for sectoral distribution of MSMEs (latest year available) . "columns": ["item","philippines","azerbaijan","georgia","kazakhstan","brunei_darussalam","lao_people’s_democratic_republic","uzbekistan","pakistan","viet_nam","samoa","sri_lanka","armenia","kyrgyz_republic","tajikistan","fiji","papua_new_guinea","nepal*","cambodia","indonesia","malaysia","myanmar","singapore","thailand","bangladesh","india*"]
        8. Use 'a4._msmes_by_region' for  regional distribution of MSMEs within countries (latest year). "columns": ["item","sri_lanka","armenia","azerbaijan","georgia","kazakhstan","kyrgyz_republic","tajikistan","uzbekistan","lao_people’s_democratic_republic","thailand","malaysia","bangladesh","cambodia","philippines","pakistan","samoa","brunei_darussalam","indonesia","myanmar*","singapore","viet_nam","india*","nepal*","fiji","papua_new_guinea"]
        9. Use 'a5._number_of_employees_by_msmes' for employment numbers in MSMEs over time by country. "columns": ["country","2003","2004","2005","2006","2007","2008","2009","2010","2011","2012","2013","2014","2015","2016","2017","2018","2019","2020","2021","2022"] 
        10. Use 'a6._msme_employees_to_total' for the percentage of total employment represented by MSMEs. "columns": ["country","2003","2004","2005","2006","2007","2008","2009","2010","2011","2012","2013","2014","2015","2016","2017","2018","2019","2020","2021","2022"]
        11. Use 'a7._msme_employees_by_sector' for which sectors employ the most MSME workers (latest year). "columns": ["item","georgia","kazakhstan","lao_people’s_democratic_republic","viet_nam","uzbekistan","philippines","brunei_darussalam","azerbaijan","india*","nepal","pakistan*","sri_lanka","armenia","kyrgyz_republic","tajikistan","fiji","papua_new_guinea","samoa","cambodia","indonesia","malaysia","myanmar","singapore","thailand","bangladesh"]
        12. Use 'a8._msme_employees_by_region' for regional employment share in MSMEs (latest year). "columns": ["item","malaysia","thailand","sri_lanka","armenia","azerbaijan","georgia","kazakhstan","kyrgyz_republic","cambodia","uzbekistan","bangladesh","papua_new_guinea","philippines","samoa","brunei_darussalam","indonesia","lao_people’s_democratic_republic","myanmar","singapore","viet_nam","india*","nepal","pakistan","tajikistan","fiji"]
        13. Use 'a9_1._gdp_of_msmes_(local_currency)' for GDP contribution of MSMEs in local currencies over time. "columns": ["country","2003","2004","2005","2006","2007","2008","2009","2010","2011","2012","2013","2014","2015","2016","2017","2018","2019","2020","2021","2022","unit:"]
        14. Use 'a9_2._gdp_of_msmes_(million)' for MSME GDP in USD across countries over time. "columns": "columns": ["country","2003","2004","2005","2006","2007","2008","2009","2010","2011","2012","2013","2014","2015","2016","2017","2018","2019","2020","2021","2022"]
        15. Use 'a10._msme_contribution_to_gdp' for percentage of GDP generated by MSMEs per country.  "columns": ["country","2003","2004","2005","2006","2007","2008","2009","2010","2011","2012","2013","2014","2015","2016","2017","2018","2019","2020","2021","2022"]
        16. Use 'a11._msme_gdp_by_sector' for sectors contribute most to MSME GDP (latest year). "columns": ["item","kyrgyz_republic","georgia","cambodia","indonesia","lao_people’s_democratic_republic","malaysia","myanmar","philippines","singapore","thailand","viet_nam","bangladesh","india","nepal","pakistan","sri_lanka","armenia","azerbaijan","kazakhstan","tajikistan","uzbekistan","fiji","papua_new_guinea","samoa","brunei_darussalam"
        17. Use 'a13_1._msme_export_value_(local_currency)' for MSME export value in local currencies over time. "columns": ["country","2003","2004","2005","2006","2007","2008","2009","2010","2011","2012","2013","2014","2015","2016","2017","2018","2019","2020","2021","2022","unit:" ] 
        18. Use 'a13_2._msme_export_value_(million)' for MSME exports in USD across countries over time.  "columns":["country","2003","2004","2005","2006","2007","2008","2009","2010","2011","2012","2013","2014","2015","2016","2017","2018","2019","2020","2021","2022"]
        19. Use 'a14._msme_exports_to_total' for the percentage of total exports contributed by MSMEs. "columns": ["country","2003","2004","2005","2006","2007","2008","2009","2010","2011","2012","2013","2014","2015","2016","2017","2018","2019","2020","2021","2022"]
        20. Use 'a1._number_of_msmes' for total number of MSMEs per country over years. "columns": "columns": ["country","2003","2004","2005","2006","2007","2008","2009","2010","2011","2012","2013","2014","2015","2016","2017","2018","2019","2020","2021","2022"]
        21 .Use `nifty_sme_emerge` for Nifty SME Emerge related over time contains open, high ,low ,close columns": ["index_name", "date", "open", "high","low","close"]
        Consider the list above, and respond ONLY with one of the file names from the following list:
        [bdi(1),cleaned_adb_asia_sme,exchange_rate_lcy_usd,gdp_(current_prices),state_wise_udyam_registration,a2._msmes_to_total,a3._msmes_by_sector,a4._msmes_by_region,a5._number_of_employees_by_msmes,a6._msme_employees_to_total,a7._msme_employees_by_sector,a8._msme_employees_by_region,a9_1._gdp_of_msmes_(local_currency),a9_2._gdp_of_msmes_(million),a10._msme_contribution_to_gdp,a11._msme_gdp_by_sector,a13_1._msme_export_value_(local_currency),a13_2._msme_export_value_(million),a14._msme_exports_to_total,a1._number_of_msmes,nifty_sme_emerge,none_of_these]
        DO NOT include any reasoning traces or other text apart from the file name selected from the above list.
            """),
            temperature=0.01,
            ),
        contents=query
    )
    
    return response.text

def task_descriptions_by_file_CPI(selected_file):
    selected_file = selected_file.strip()
    description = {"cpi_inflation_data":""" 
    Columns are => ["year","month","month_numeric","state","sector","group_name","sub_group_name","inflation_index","inflation_rate","data_release_date","data_updated_date","data_source"]           
    Note:For cpi_inflation_always return all fields information for example: "data_source","data_release_date","data_updated_date" etc 
    When setting conditions for column values, always refer to the following list for cpi_inflation_data table. This list contains the exact string matches to ensure SQL query conditions are accurate. By  following this, you can avoid any mistakes while generating SQL queries: 
    1. 'year': Choose any year from 2013 onwards. For example, 2013, 2019, 2025.                                                                                                                                     
    2. 'month': Choose one or more months of the year in word form. For example, January, August.                                                                                                                    
    3. 'month_numeric': Choose any value between 1 and 12 depending on the corresponding month(s).                                                                                                                   
    4. 'state': Choose one or more of the states of India. Note that "All India" is a special key relating to data for the national or country level aggregate queries.                                              
    5. 'sector': Choose one from the following list: ["Combined", "Rural", "Urban"]   
    6. 'group_name': Choose one or more from the following list: ["Food and Beverages","Pan, Tobacco and Intoxicants","Housing","Clothing and Footwear","Consumer Food Price","Miscellaneous","General","Consumer Food Price","Fuel and Light"]. Note that "General" is a special key for aggregate queries. 
    7. 'sub_group_name': Choose one or more from the following list IF you are looking under food and beverages: ["*", "Cereals and Products", "Meat and Fish", "Egg", "Milk and Products", "Oils and Fats","Fruits", "Vegetables", "Pulses and Products", "Sugar and Confectionery", "Spices", "Prepared Meals, Snacks, Sweets etc.", "Non-alcoholic Beverages"]. 
    8. 'sub_group_name': Choose one or more from the following list IF you are looking under clothing and footwear: ["*", "Clothing", "Footwear"]. 
    9. 'sub_group_name": Choose one or more from the following list IF you are looking under miscellaneous group: ["*", "Household Goods and Services", "Health", "Transport and Communication", "Recreation and Amusement", "Education", "Personal Care and Effects"].
    10. For all 'group_name' options, the 'sub_group_name' called "*" is available, and can be used for aggregate queries.  
    

    **Query Construction Rules:**
                   1. Always keep the state as "All India" if not specified in the question by user, query.                                                                                                                                         
                   2. Always keep the sector as "Combined" if not specified in the question by user.                                                                                                                                         
                   3. Always keep the group_name as "General" if not specified in the question.                                                                                                                                      
                   4. Always keep the sub_group_name as "*" if not specified in the question by user.     
                   5. If a question asks about India and does not provide state then use state as "All India".                                                                                                                                    
                   6. Never provide information about the urban and rural sector if not specified in the question.
                   7. If the question does ask about urban or rural but does not mention state, then use state as "All India".
                   8. If the question asks about ranking by state, ensure you sort by state and request data not including "All India" as one of the states. 
                   9. If the question asks for ranking in India and state is not mentioned always use "All India" as default state.
                                    

 

Examples for the above important rules are:                                                                                                                                                                      
    a.What are the sector-wise inflation trends in Maharashtra, such as food, housing, and transportation?      
    - In this case, the state is Maharashtra, and the sector is Combined. The group_name to consider are "General","Food and Beverages","Clothing and Footwear","Miscellaneous" , and the sub_group_name is * ,  "Transport and Communication" .
    -No need to provide infomation about rural and urban sector as nothing is mentioned in the question. 
    b.Inflation trends in Tamil Nadu over the last three years:                                                                                                                                                          
    - In this case, the state is Tamil Nadu, and the sector is Combined. The group_name to consider is "General" and the sub_group_name is "*".                                                                      
    -No need to provide infomation about rural and urban sector as nothing is mentioned in the question.                                                                                                             
    -Provide the data for the recent three years.E.g. 2023,2024,2025.  
    
Follow below rules (Important Rules):
    1. **WHEN A QUESTION IS AMBIGUOUS (MISSING YEAR, MONTH, SECTOR, OR GROUP_NAME  or sub_group_name or state) :**
    - CHOOSE THE **LATEST YEAR** .
    - DEFAULT **sector = "Combined"**, **group_name = "General"**, **sub_group_name = "*" , state="All India"**.
        Example 1: whats is the inflation rate of india then choose state=all india , sector=combined , group_name=general and sub_group_name=*.
        Example 2 :Retrieve inflation rate for months between 2023 to 2025 then as nothing is specfied in the question then choose state=all india , sector=combined , group_name=general and sub_group_name=*.
    2. **ENSURE ALL SELECT STATEMENTS INCLUDE THE FOLLOWING FIELDS:**
    - `year`, `month`, `month_numeric`, `state`, `sector`, `group_name`, `sub_group_name`.
    - Queries **must be fully structured and accurate**.

    3. **DEFAULT CONDITIONS (UNTIL SPECIFIED OTHERWISE IN THE QUESTION):**
    - `WHERE year = MAX(year) AND month_numeric = MAX(month_numeric) AND state = 'All India' AND sector = 'Combined' AND sub_group_name = '*'`.
                
Some more rules:
    - If a user asks for **inflation** (e.g., *"What is the inflation rate in Gujarat?"*):
    - Use **`group_name = 'General'`**
    - Use **`sub_group_name = '*'`**
    - Use **`sector = 'Combined'`** (unless another sector is mentioned)
    -choose maximum year and maximum month , MAX(year) , MAX(month_numeric)

    - For group_name="Food and Beverages" , understand what user is asking for:
    -  Use **`sector = 'Combined'`** (unless another sector is specified like rural or urban)
    - Use **`group_name = 'Food and Beverages'`**
    - Use **`sub_group_name = '*'`** (unless a specific sub-group is requested)
    - There exists sub-group names like ""Cereals and Products" ,"Meat and Fish","Egg","Milk and Products","Oils and Fats","Fruits","Vegetables","Pulses and Products","Sugar and Confectionery","Spices","Prepare  Meals, Snacks, Sweets etc.","Non-alcoholic Beverages". 
    -Example:What is the inflation rate for Vegetables?
        - Use **`group_name = 'Food and Beverages'`**
        - Use **`sub_group_name = 'Vegetables'`**
        - Use **`sector = 'Combined'`** (unless another sector is specified)
    If a query requests a specific year range
    -For example: Provide inflation rate for year 2023 to 2024.
    -Provide only general combined inflation rate for year 2023 to 2024.
    -There is no need to include inflation rates for all sub_group_name and group_name.
    -Similarly, if the question requests the inflation rate for months between 2023 and 2025 without specifying additional details, choose All India as the state, Combined as the sector, General as the group_name, and * as the sub_group_name 
        -Example 1: what are the monthly inflation rates for feb 2022 to feb 2023, then keep the state as all india , sector as combined and group_name as general and sub_group_name as *.
    -Example 2 :Retrieve inflation rate for months between 2023 to 2025 then as nothing is specfied in the question then choose state=all india , sector=combined , group_name=general and sub_group_name=*.
    -Example 3:  In cases where the question compares the inflation rates of specific categories, such as Meat and Fish versus Vegetables for All India in 2023, use Combined as the sector since urban or rural distinctions are not mentioned. 
        -Also month should be 2,3,4,5,...11,12,1,2 and year should be 2023 to 2024.
    -In this kind of case , Carefully execute the query and and if data for the requested period is , not available then inform user about this "not available data instead of null".

    -If question is like:
    Example1 => what are the sub category inflation rate for Kerala for the month of January 2025 , then in this case , state should be kerala and sector should be combined only and group_name should be all   unique  and sub_group_name should be *. 
                """,
    "consumer_price_index_CPI_for_agricultural_and_rural_labourers": """
SOURCE="India Budget Ecconomic Survey"
This table contains the Consumer Price Index (CPI) for Agricultural and Rural Labourers in India. The data is categorized by state, year , month , category ,index_value,labour_type.
Columns are => ["id", "state", "year", "month", "category", "index_value", "labour_type", data_release_date","data_updated_date","data_source"]

Note: For consumer_price_index_cpi_for_agricultural_and_rural_labourers always return all fields information.

When setting conditions for column values, always refer to the following list for consumer_price_index_cpi_for_agricultural_and_rural_labourers table. This list contains the exact string matches to ensure SQL query conditions are accurate. By following this, you can avoid any mistakes while generating SQL queries:

1. 'id': Unique identifier for each record (integer).
2. 'state': Choose one or more of the states of India from the following list.["rajasthan", "haryana", "bihar", "meghalaya", "jammukashmir", "maharashtra", "madhyapradesh", "assam", "andhrapradesh", "himachalpradesh", "allindia", "punjab", "manipur", "gujarat", "odisha","tripura", "karnataka", "jammu&kashmir", "kerala", "westbengal", "uttarpradesh", "tamilnadu"]
3. 'year': Choose any year for which data is available. For example, 2024.
4. 'month': Choose one or more months of the year in word form. For example, "June", "July".
5. 'category': Choose one or more from the following list: ["General", "Food"].
6. 'index_value': This is the CPI index value (numeric).
7. 'labour_type': Choose one from the following list: ["rural","agricultural"].

Some Very Important Rules:

    1. Always keep the state as "All India" if not specified in the question. (However, note that "All India" is NOT present as a valid value in the 'state' column.) So you have to choose from available states only.
    2. When a question is ambiguous (missing year, month, state, category, or labour_type):
    - Choose the **LATEST YEAR**.
    - Choose the **latest month**.
    - If the `state` is not specified, choose available state.
    - Default `category = "General"`.
    - Default `labour_type = "rural"`.

    3. Ensure all SELECT statements include the following fields: `id`, `state`, `year`, `month`, `category`, `index_value`, `labour_type`.

    4. Default Conditions (until specified otherwise in the question):
    - `WHERE year = MAX(year) AND month = MAX(month) AND state = <available_state> AND category = 'General' AND labour_type = 'rural'`

Some more rules:

    - If a user asks for the "CPI" or "Consumer Price Index," and the state is specified:
    - Use `category = 'General'`
    - Use `labour_type = 'rural'`
    - Choose maximum year and maximum month, MAX(year), MAX(month).

    - If the question asks about a specific category (e.g., "Food"):
    - Use `category = 'Food'`
    - Use `labour_type = 'rural'` (unless another labour_type is specified).
    - Choose maximum year and maximum month, MAX(year), MAX(month).

    - If a query requests a specific year range:
    - For example: "Provide CPI for the years 2023 to 2024."
    - Provide only the `General` category CPI rate for the specified year range.
    - There is no need to include CPI for all categories.
    - If data for the requested period is not available, inform the user about this "not available data" instead of returning null.

    - If the question is like: "What is the CPI for Andhra Pradesh for the month of June 2024?"
    - Then, state should be "andhrapradesh", category should be "General", and labour_type should be "rural."
                    """,
    "city_wise_housing_price_indices": """
SOURCE="India Budget Ecconomic Survey"
Columns are => ["id", "city", "index_value", "year", "quarter", data_release_date","data_updated_date","data_source"]
Note:For city_wise_housing_price_indices always return all fields information for example: "id","city","index_value" etc
When setting conditions for column values, always refer to the following list for city_wise_housing_price_indices table. This list contains the exact string matches to ensure SQL query conditions are accurate. By following this, you can avoid any mistakes while generating SQL queries:
1. 'id': Unique identifier for each record. It's an integer.
2. 'city': The name of the city for which the housing price index is recorded. Examples: ["Meerut", "Kalyan Dombivali", "Panvel", "Jaipur", "Vasai Virar", "Patna", "Navi Mumbai", "Kochi", "Noida",
          "Hyderabad", "Bidhan Nagar (Excluding Rajarhat)", "Indore", "Gurugram", "Vijayawada", "New Town Kolkata",
          "Mumbai", "Mira Bhayander", "Pimpri Chinchwad", "Delhi", "Pune", "Bhopal", "Vizag", "Greater Noida", "Thane",
          "Guwahati", "Raipur", "Dehradun", "Bengaluru", "Ludhiana", "Lucknow", "Thiruvananthapuram", "Nagpur",
          "Bhubaneswar", "Ghaziabad", "Kolkata", "Chandigarh (Tricity)", "Ahmedabad", "Coimbatore", "Surat", "Kanpur",
          "Vadodara", "Howrah", "Ranchi", "Rajkot", "Gandhinagar", "Chakan", "Chennai", "Bhiwadi", "Nashik", "Faridabad"].
3. 'index_value': The housing price index value. It's a numerical value representing the price index. Example: 91, 76, 104.
4. 'year': The year the housing price index was recorded. Choose any year from the available data, e.g., 2013.
5. 'quarter': The quarter of the year the housing price index was recorded. Examples: "Q1", "Q2", "Q3", "Q4".

Some Very Important Rules:
1. When a question is ambiguous (missing year or city):
- Choose the latest year.
- If the city is not specified, it depends on the specific question. There's no default "All India" equivalent here.

2. Ensure all SELECT statements include the following fields:
- `id`, `city`, `index_value`, `year`, `quarter`.
- Queries must be fully structured and accurate.

3. Default conditions (until specified otherwise in the question):
- `WHERE year = MAX(year)` (and any other relevant defaults). There is no all india equivalent here

Some more rules:

- If a user asks for housing price indices in general (e.g., "What is the housing price index in Ahmedabad?"):
- You need to specify the city.
- choose maximum year MAX(year) if year is not specified.

- If a query requests a specific year range
-For example: Provide housing price indices for the year 2013 to 2014.
- If data for the requested period is not available, then inform user about this "not available data instead of null".


-If question is like:
Example1 => what is the housing price index for Bhiwadi for the year 2013 , then in this case , city should be bhiwadi and year should be 2013.
IMPORTANT STRICT RULES:
                When writing the SQL, you MUST use the exact strings copied character-by-character from the given list for the item column.
                Most important: Avoid deeply nested JSON. Keep any lists or dictionaries shallow (max one level).
                Provide all the fields values in the output json.
                If "value" is 0 => convert it to "NA"
    """,
    "whole_sale_price_index_WPI_financial_year_wise": """
        SOURCE="India Budget Ecconomic Survey"
Columns are => ["id", "commodity_name", "commodity_code", "commodity_weight", "year", "index_value", data_release_date","data_updated_date","data_source"]
Note:For whole_sale_price_index_wpi_financial_year_wise always return all fields information for example: "id","commodity_name","commodity_code" etc
When setting conditions for column values, always refer to the following list for whole_sale_price_index_wpi_financial_year_wise table. This list contains the exact string matches to ensure SQL query conditions are accurate. By  following this, you can avoid any mistakes while generating SQL queries:
1. 'id': This is a unique identifier for each record. Choose any valid integer ID.
2. 'commodity_name': Choose one or more commodity names. For example, "all commodities", "primary articles", "food articles".
3. 'commodity_code': Choose any valid commodity code. For example, 1000000000, 1100000000, 1101000000.
4. 'commodity_weight': Choose any commodity weight. For example, 100, 22.6176, 15.2559.
5. 'year': Choose any year for which data is available. For example, 2012.
6. 'index_value': Choose any index value corresponding to the commodity and year. For example, 106.9, 111.4, 110.9.

Some Very Important Rules:
1.If not specified in the question, choose the latest year.
2.There is no concept of state, sector, group_name, or sub_group_name in this table.
3.The table contains data at a national level.

Some examples for the above important rules are:
a.What is the index value for food articles?
    - In this case, choose the latest year, and commodity_name is "food articles".

Follow below rules (Important Rules):
1. **WHEN A QUESTION IS AMBIGUOUS (MISSING YEAR OR COMMODITY_NAME) :**
- CHOOSE THE **LATEST YEAR** .
Example :Retrieve index value.Then choose the latest year and all commodities.
2. **ENSURE ALL SELECT STATEMENTS INCLUDE THE FOLLOWING FIELDS:**
- `id`, `commodity_name`, `commodity_code`, `commodity_weight`, `year`, `index_value`.
- Queries **must be fully structured and accurate**.

3. **DEFAULT CONDITIONS (UNTIL SPECIFIED OTHERWISE IN THE QUESTION):**
- `WHERE year = MAX(year)` .

- If a user asks for the index value of a commodity (e.g., *"What is the index value for all commodities?"*):
- Use **`commodity_name = 'all commodities'`** (unless another commodity is mentioned)
-choose maximum year , MAX(year)

-If a query requests a specific year range
-For example: Provide index value for year 2012.
-Provide only index value for the given year .
-There is no need to include all other fields
-Similarly, if the question requests the index value for a commodity for a specific year.
Example1 => what are the index value for food articles for the year 2012, then in this case , year should be 2012 and commodity_name should be food articles

-If question is like:
Example1 => what is the index value for food articles for the year 2012 , then in this case , year should be 2012 and commodity_name should be food articles.


    """,
    "cpi_worker_data": """
        SOURCE="INDIA BUDGET;economic survey report"

    Columns are => ["id", "year", "time_period", "worker_type", "base_year", "worker_region", "index_value", data_release_date","data_updated_date","data_source"]
    Note:For cpi_worker_data always return all fields information for example: "id","year","time_period" etc
    When setting conditions for column values, always refer to the following list for cpi_worker_data table. This list contains the exact string matches to ensure SQL query conditions are accurate. By following this, you can avoid any mistakes while generating SQL queries:
    1. 'id': Unique identifier for each record. This is an integer and can be used as a primary key.
    2. 'year': The year for which the data is recorded. Choose any year from available data, for example, 2011, 2012, 2013.
    3. 'time_period': Indicates the time period for the data. It could be "Average of Months" or other specific periods available in the dataset.
    4. 'worker_type': Specifies the type of worker for which the data is relevant. Example: ["CPI-RL","CPI-AL","CPI-NS","CPI-IW"].
    5. 'base_year': The base year used for calculating the index value. Example: 2001,2012,1986,2001,2010,2016.
    6. 'worker_region': The region to which the worker data pertains. Example: "Food" , "Rural" ,"General" ,"Urban" ,"Combined" ,"Non Food".
    7. 'index_value': The Consumer Price Index (CPI) value. This is a numerical value representing the index.

    Some Very Important Rules:
    1. **WHEN A QUESTION IS AMBIGUOUS (MISSING YEAR, TIME_PERIOD, WORKER_TYPE, BASE_YEAR, or WORKER_REGION):**
    - CHOOSE THE **LATEST YEAR** .
    - DEFAULT **time_period = "Average of Months"**, **worker_type = "CPI-IW"**, **worker_region = "General"**.

    2. **ENSURE ALL SELECT STATEMENTS INCLUDE THE FOLLOWING FIELDS:**
    - `id`, `year`, `time_period`, `worker_type`, `base_year`, `worker_region`, `index_value`.
    - Queries **must be fully structured and accurate**.

    3. **DEFAULT CONDITIONS (UNTIL SPECIFIED OTHERWISE IN THE QUESTION):**
    - `WHERE year = MAX(year) AND time_period = 'Average of Months' AND worker_type = 'CPI-IW' AND worker_region = 'General'`

    Some more rules:
    - If a user asks for CPI index values (e.g., *"What is the CPI index value in 2012?"*):
    - Consider `worker_region = 'General'`
    - Consider `worker_type = 'CPI-IW'`
    - choose maximum year if the year is not mentioned.

    - If a query requests a specific year range:
    - For example: Provide CPI index values for the year 2011 to 2013.
    - Provide CPI index values for specified years only.
    - If data for the requested period is not available, then inform the user about this "not available data instead of null".

    - If the question is like:
    Example1 => What is the CPI index value for 2012, then in this case, year should be 2012 and time_period should be "Average of Months", worker_type should be "CPI-IW", and worker_region should be "General".

    """,                                                                                                                                                                                                             
    "whole_sale_price_index_WPI_calendar_wise": """
        SOURCE="India Budget Ecconomic Survey"                                                                                                                                                   
        Columns are => ["id", "commodity_name", "commodity_code", "commodity_weight", "year", "index_value", data_release_date","data_updated_date","data_source"]

    Note: For whole_sale_price_index_wpi_calendar_wise table always return all fields information for example: "id","commodity_name","commodity_code" etc.

    When setting conditions for column values, always refer to the following list for whole_sale_price_index_wpi_calendar_wise table. This list contains the exact string matches to ensure SQL query conditions are accurate. By following this, you can avoid any mistakes while generating SQL queries:

    1. 'commodity_name': Choose one or more commodity names from the available list such as "all commodities", "primary articles","food articles","food grains (cereals+pulses)","cereals","paddy","wheat","jowar","bajra" ,"maize" ,"barley" ,"ragi","pulses","gram",
                  "arhar","moong","masur","urad","peas/chawali","rajma","fruits & vegetables","vegetables","potato" , "all commodities",.......etc etc]
    2. 'commodity_code': Choose a valid commodity code. For example, 1000000000, 1100000000, 1101000000.
    3. 'commodity_weight': Choose a valid commodity weight. For example, 100, 22.6176, 15.2559.
    4. 'year': Choose any year for which data is available. For example, 2013, 2021, 2020, 2015, 2023, 2022, 2014, 2017, 2019, 2016, 2012, 2018 .
    5.  'index_value': This column represents the Wholesale Price Index (WPI) value.

    Some Very Important Rules:

    1. WHEN A QUESTION IS AMBIGUOUS (MISSING YEAR, COMMODITY_NAME, COMMODITY_CODE):
    - CHOOSE THE LATEST YEAR.
    - You can not assume any default values for commodity_name, commodity_code and commodity_weight if they are not specified in the question.

    2. ENSURE ALL SELECT STATEMENTS INCLUDE ALL THE COLUMNS FROM THE TABLE:
    - Queries must be fully structured and accurate.

    3. DEFAULT CONDITIONS (UNTIL SPECIFIED OTHERWISE IN THE QUESTION):
    - WHERE year = MAX(year).

    Some more rules:

    - If a user asks for WPI(e.g., "What is the WPI for all commodities?"):
    - Use `commodity_name = 'all commodities'` if the question refers to all commodities.

    Examples:
    a. What is the index value for food articles in 2013?
    - In this case, the commodity_name is "food articles", and the year is 2013.

    b. WPI trends for primary articles over the years:
    - In this case, the commodity_name is "primary articles". Provide the data for all available years.

    Description of Columns:

    - `id`: A unique identifier for each record in the table.
    - `commodity_name`: The name of the commodity for which the wholesale price index is recorded (e.g., all commodities, primary articles, food articles).
    - `commodity_code`: A numerical code representing the commodity.
    - `commodity_weight`: The weight assigned to the commodity in the WPI calculation.
    - `year`: The year for which the WPI is recorded. Choose any valid year available in the table.
    - `index_value`: The wholesale price index value for the commodity in the given year.

    Querying Instructions:

    - When querying this table, you can filter based on `commodity_name`, `commodity_code`, `commodity_weight`, and `year`.
    - If the year is not specified, default to the maximum available year in the dataset.
    - There are no specific "state", "sector", "group_name", or "sub_group_name" equivalents in this table. Therefore, the rules related to those fields in the `cpi_inflation_data` table do not apply here.
    - Ensure that all selected columns are included in the SELECT statement.

    Some more rules:

    *   If a user asks for the WPI of a specific commodity (e.g., *"What is the WPI for food articles?"*):

        *   Use `commodity_name = 'food articles'`

    *   If the question requests a specific year range:

        *   For example: "Provide the WPI for all commodities for the years 2013 to 2015."
        *   Provide the WPI for 'all commodities' for each year in the specified range.
        *   There is no need to include WPI for all commodity names if not specified.

    *   If the question compares WPI of different commodities within a specific year:

        *   For example: "Compare the WPI of food articles and manufactured products in 2013."
        *   Provide the WPI for both 'food articles' and 'manufactured products' for the year 2013.

    *   If question is like:

        *   Example 1 => What is the WPI for all commodities? Then, in this case, use commodity_name = "all commodities" and year = MAX(year).
    """,
    "none_of_these": """This query does not relate to any of the files present in the database. IMPORTANT: Return a valid JSON with the message "Data is not present." """}
    try:
        print("Attempting to find: " + selected_file)
        return description[selected_file]
    except:
        return "I did not find this file in my list of task descriptions."
    
def task_descriptions_by_file_GDP(selected_file):
    selected_file = selected_file.strip()
    description = {
        "annual_estimate_gdp_crore":"""
                DATA SOURCE => MoSPI

                Use this table when the query asks for the actual GDP value (in ₹ crores).(i.e If the query is about “how much” a sector or economic indicator contributed to GDP (in ₹ crores) — use this table.)
                Important => When setting conditions for column values, always refer to the  list given along with column information. This list contains the exact string matches to ensure SQL query conditions are accurate. By following this, you can avoid any mistakes while generating SQL queries

                Columns are:
                -items =>Represents either an economic sector or a GDP component.These component/sector includes ["Trade, Hotels, Transport, Communication & Services related to Broadcasting","Net taxes on Products  ","Manufacturing","Construction","Net taxes on Products","PFCE","Public Administration, Defence & Other Services","GFCE","Tertiary Sector","GVA at Basic Prices","Imports of goods and services ","GNI  ","CIS","NNI ","Financial, Real Estate & Professional Services","Mining & Quarrying","Discrepancies ","Secondary Sector","NVA at Basic Prices","Agriculture, Livestock, Forestry & Fishing","GFCF","GNI ","Exports of goods and services","Electricity, Gas, Water Supply & Other Utility Services","Imports of goods and services","Valuables","GDP ","Per capita income(Rs.)","Primary Sector"]
                -columns names are = ["items" ,"price_type","time_period","years","value"]
                -time_period =>  "annual"
                -price_type => ["constant" ,"current"]
                -value => represents gdp estimate of the item/sector in crores.
                -years => ["2016-17","2014-15","2018-19","2013-14","2024-25","2022-23","2017-18","2011-12","2021-22","2012-13","2020-21","2015-16","2019-20","2023-24"]
                Note:Take more help from Keyword Section
        
                * For annual_estimate_gdp_crore table:
                a.Identify query is asking for sector or gdp component .
                b.Differentiate between gdp component and economic sectors , and carefully set the item in 'WHERE' clause for asnwering the query.
                An economic sector (e.g., Primary, Secondary, Tertiary, Manufacturing)
                A GDP component (e.g., GVA, NNI, PFCE, Imports)

                IMPORTANT STRICT RULES:
                When writing the SQL, you MUST use the exact strings copied character-by-character from the given list for the item column.
                Most important: Avoid deeply nested JSON. Keep any lists or dictionaries shallow (max one level).
                Provide all the fields values in the output json.
                If "value" is 0 => convert it to "NA"

                Common Use Cases:
                -"What was the GDP of the Manufacturing sector in 2022-23?"
                -"How much was the Per Capita Income in 2020-21?"
                -"Give the value of Gross Fixed Capital Formation (GFCF) in 2023-24."
                -"What was the contribution of Agriculture to the economy in 2019-20?"
                   """,
        "annual_estimate_gdp_growth_rate": """
                Use this table when your question is about how fast or slow a sector/component is growing. It contains percentage growth rates instead of actual GDP values.
                DATA SOURCE => MoSPI
                Important => When setting conditions for column values, always refer to the  list given along with column information. This list contains the exact string matches to ensure SQL query conditions are accurate. By following this, you can avoid any mistakes while generating SQL queries
                
                Columns are:
                -items-Represents either an economic sector or a GDP component.These component/sector includes  ["Trade, Hotels, Transport, Communication & Services related to Broadcasting","Agriculture, Livestock, Forestry & Fishing","Manufacturing","GFCF","Construction","3.3 Public Administration, Defence & Other Services","GNI ","Net taxes on Products","Public Administration, Defence & Other Services","PFCE","GFCE","Tertiary Sector","Exports of goods and services","GVA at Basic Prices","Electricity, Gas, Water Supply & Other Utility Services","CIS","Imports of goods and services","Valuables","GDP ","NNI ","Financial, Real Estate & Professional Services","Mining & Quarrying","Discrepancies ","Per capita income(Rs.)","Secondary Sector","NVA at Basic Prices","Primary Sector"]
                -column names are = ["items","price_type","time_period","years","value"]
                -price_type => can be "constant" or "current".
                -time_period =>  ["annual"]
                -value => represents gdp growth rate of the item/sector .
                -years =>["2014-15","2018-19","2013-14","2024-25","2022-23","2017-18","2011-12","2021-22","2012-13","2020-21","2015-16","2019-20","2023-24"]
                Note:Take more help from Keyword Section

                * For annual_estimate_gdp_growth_rate table:
                    a.Identify query is asking for sector or gdp component .
                    b.Differentiate between gdp component and economic sectors , and carefully set the item in 'WHERE' clause for asnwering the query.

                IMPORTANT STRICT RULES:
                When writing the SQL, you MUST use the exact strings copied character-by-character from the given list for the item column.
                Most important: Avoid deeply nested JSON. Keep any lists or dictionaries shallow (max one level).
                Provide all the fields values in the output json.
                If "value" is 0 => convert it to "NA"

                Key Use Cases: -"What was the growth rate of the Manufacturing sector in 2022-23?"
                -"Compare the GDP growth rate of Primary vs Secondary sector over the past 5 years."
                -"Which sector had the highest annual growth in 2020-21?"
                -"What is the growth trend of GVA at constant prices?"
                """,
        "gross_state_value": """
                DATA SOURCE => MoSPI
                You should use the gross_state_value table when the query is about state-level economic performance — specifically when it refers to the value generated by sectors within individual states (GVA) or asks for Gross State Domestic Product (GSDP).
                Important => When setting conditions for column values, always refer to the  list given along with column information. This list contains the exact string matches to ensure SQL query conditions are accurate. By following this, you can avoid any mistakes while generating SQL queries

                Columns:
                -Represents the Gross State Value Added (GSVA) for each sector in crores for the year.These sectors are ["Electricity, gas, water supply & other utility services","Fishing and aquaculture","Storage","Manufacturing","Financial services","Construction","Trade, repair, hotels and restaurants","Tertiary","Road transport#","Population","Livestock","Agriculture, forestry and fishing","Air transport","Road transport","Primary","Transport, storage, communication & services related to broadcasting","Road transport*","Trade & repair services**","Other services","Water transport","Per Capita GSDP","TOTAL GSVA at basic prices","Taxes on Products#","Railways","Public administration","Trade & repair services ","Crops","Communication & services related to broadcasting","Real estate, ownership of dwelling & professional services","Taxes on Products","Mining and quarrying","Gross State Domestic Product","Trade & repair services","Services incidental to transport","Secondary","Subsidies on products","Forestry and logging","Hotels & restaurants",]
                -column names are ["state","gross_state_value_added_at","sector","year","value"]
                -gross_state_value_added_at => can be ["constant price" , "current price"]
                -year => ["2019-20","2017-18","2011-12","2023-24","2021-22","2012-13","2020-21","2016-17","2014-15","2018-19","2015-16","2013-14","2022-23"]
                Note:Take more help from Keyword Section

                Use this table when the query:
                    -Asks for GVA or GSDP of a specific Indian state (like Uttar Pradesh, Kerala, etc.)
                    -Refers to state-wise sectoral performance (e.g., manufacturing in Gujarat, agriculture in Punjab)
                    -Mentions Per Capita GSDP or GSVA at current/constant prices for a state
                    -Asks for comparison of sectors across different states

                IMPORTANT STRICT RULES:
                When writing the SQL, you MUST use the exact strings copied character-by-character from the given list for the item column.
                Most important: Avoid deeply nested JSON. Keep any lists or dictionaries shallow (max one level).
                Provide all the fields values in the output json.
                If "value" is 0 => convert it to "NA"

                Key Use Cases:
                -"What was the GSDP of Maharashtra in 2022-23?"
                -"Compare the manufacturing output of Gujarat and Tamil Nadu."
                -"How much did agriculture contribute to the economy of Punjab in 2019-20?"
                -"Give me the Per Capita GSDP of Kerala for 2021-22."
                -"List top 5 states by GVA in Trade & repair services in 2023-24."
                    """,
        "key_aggregates_of_national_accounts": """
                DATA SOURCE => MoSPI
                If the query is about macroeconomic indicators (savings, income, consumption, capital formation, ROW transfers) at the national level, use key_aggregates_of_national_accounts.
                Important => When setting conditions for column values, always refer to the  list given along with column information. This list contains the exact string matches to ensure SQL query conditions are accurate. By following this, you can avoid any mistakes while generating SQL queries

                -column names are =["year","item","value","price_type","value_category"]
                -item => Refers to the economic metric or component being measured , these are ["Gross Saving","GVA at basic prices","Less Imports of goods and services","Import of goods","Less Subsidies on Products","GDP","Export of goods","PFCE","GFCE","Primary income receivable from ROW (net)","Import of services","CIS","GNI","Export of services","Export of goods and services","GNDI","Taxes on Products including import duties","CFC","VALUABLES","GCF","Net Saving","NNDI","Rates","GFCF","Less Import of goods and services","GCF  excluding Valuables to GDP","Other current transfers (net) from ROW","GCF to GDP","Gross Saving to GNDI","NNI","PFCE to NNI","Exports of goods and services","NDP","Valuables","Discrepancies"]
                -value => Represents the value of the item in crores
                -price_type => Specifies the price basis for the data, can be ["current price" , "constant price" ]
                -value_category=> Denotes the broad economic category the item, value belongs to,Economic grouping (e.g., Domestic Product, Final Expenditure, Rates) and can be ["Domestic Product" ,"Rates of Expenditure Components to GDP" ,"Percentage Change over Previous Year","Rates","Final Expenditure"]
                -year => ["2019-20","2017-18","2011-12","2021-22","2012-13","2020-21","2016-17","2014-15","2018-19","2015-16","2013-14","2022-23"]
                Note:Take more help from Keyword Section


                IMPORTANT STRICT RULES:
                When writing the SQL, you MUST use the exact strings copied character-by-character from the given list for the item column.
                Most important: Avoid deeply nested JSON. Keep any lists or dictionaries shallow (max one level).
                Provide all the fields values in the output json.
                If "value" is 0 => convert it to "NA"


                Use this table when the query involves:
                -High-level national economic indicators
                -Comparing components of GDP (like savings, expenditure, income)
                -Ratios/Percentages of components to GDP
                -Net income, savings, or transfers from rest of the world (ROW)
                -GCF, GFCF, NNI, GNI, NDP, GNDI, etc.
                """,
        "per_capita_income_product_final_consumption": """
                DATA SOURCE => MoSPI
                This table contains per capita estimates of key economic indicators in ₹ (Indian Rupees) or growth rate (%) for various years, along with the population used for those calculations. The indicators relate to income and consumption at both current and constant prices.
                Important => When setting conditions for column values, always refer to the  list given along with column information. This list contains the exact string matches to ensure SQL query conditions are accurate. By following this, you can avoid any mistakes while generating SQL queries

                -column names are ["year","item","population","value_category","value"]
                -item => Refers to the economic measure being reported on a per capita (per person) basis , these measures are ["Per Capita GDP","Per Capita GNI","Per Capita NNI","Per Capita GNDI","Per Capita PFCE"]
                -population => Represents the population figure (in crores) used to calculate the per capita measures
                -value_category =>Denotes the broad economic category the item ,value belongs to and can be ["current price","constant price","Percentage change over previous year at constant (2011-12) prices"]
                -value => Represents the per capita value (in ₹) for each item.
                -year => ["2019-20","2017-18","2011-12","2021-22","2012-13","2020-21","2016-17","2014-15","2018-19","2015-16","2013-14","2022-23"]
                Note:Take more help from Keyword Section

                Use this table when:
                -You need per person (per capita) estimates of:
                    Income: GNI, NNI, GDP, GNDI
                -Consumption: PFCE
                -You're comparing economic well-being across years.
                -You're calculating growth trends in income or consumption per person.
                -A query asks for "per capita" values for income, expenditure, or GDP.

                IMPORTANT STRICT RULES:
                When writing the SQL, you MUST use the exact strings copied character-by-character from the given list for the item column.
                Most important: Avoid deeply nested JSON. Keep any lists or dictionaries shallow (max one level).
                Provide all the fields values in the output json.
                If "value" is 0 => convert it to "NA"

                This table helps answer queries like:
                -What is the per capita income or GDP of India in a given year?
                -What was the growth in per capita income over the previous year?
                -What is the per capita private final consumption expenditure (PFCE)?
                -What was the population base used for these estimates?
                """,        
        "provisional_estimateso_gdp_macro_economic_aggregates": """
                DATA SOURCE => MoSPI
                
                This table contains provisional estimates of major macroeconomic aggregates like GDP, GVA, NDP, NNI, GNI, capital formation, expenditure components, and per capita values for the most recent years.

                Important => When setting conditions for column values, always refer to the  list given along with column information. This list contains the exact string matches to ensure SQL query conditions are accurate. By following this, you can avoid any mistakes while generating SQL queries

                Use this table when:
                -You need latest provisional estimates (for 2021–22, 2022–23, or 2023–24).
                -You want quick summary figures for GDP, GVA, NNI, or any national income accounting aggregates.
                -A query mentions "provisional data", "macro aggregates", or recent years.

                -column names are ["year" ,"item","category","price_type","value"]
                -item => Represents the economic metric being measured , these metrics are ["Change in stocks","Change in Stocks","Government Final Consumption Expenditure","Gross Fixed Capital Formation","Gross National Income (GNI)","Per capita NNI","Less Imports","Exports","Private Final Consumption Expenditure","Gross fixed capital formation","Private final consumption expenditure","Gross Domestic Product (GDP)","Discrepancies","Valuables","Net Domestic Product (NDP)","Net National Income (NNI)","Government final consumption expenditure","Gross Value Added (GVA) at basic prices","Per Capita NNI"]
                -price_type => can be ["Constant Prices","Current Prices"]
                -category => Specifies the broader economic category the item ,value falls under,can be ["Domestic Product","National Income","ESTIMATES AT PER CAPITA LEVEL"]
                -value => Represents the numerical value of each economic metric in crores of rupees (₹) for the year.
                -year => ["2023-24","2022-23","2021-22"]

                IMPORTANT  STRICT RULES:
                When writing the SQL, you MUST use the exact strings copied character-by-character from the given list for the item column.
                Most important: Avoid deeply nested JSON. Keep any lists or dictionaries shallow (max one level).
                Provide all the fields values in the in the output json.
                If "value" is 0 => convert it to "NA"
                
                This table helps answer questions like:
                -What is the latest GDP, GNI, NNI, or GVA?
                -What is the government/private final consumption expenditure?
                -What is the change in stocks or gross fixed capital formation?
                -What is the per capita NNI for 2023-24?
                """,
        "quaterly_estimates_of_expenditure_components_gdp": """
                DATA SOURCE => MoSPI

                This table gives quarter-wise estimates of expenditure components of GDP for multiple years, at both:Current Prices (nominal, without inflation adjustment),Constant Prices (real, inflation-adjusted).It includes major components like:Private/Government Final Consumption Expenditure,Gross Fixed Capital Formation,Imports & Exports of goods/services,Change in stocks,Discrepancies,Valuables,GDP.
                Important => When setting conditions for column values, always refer to the  list given along with column information. This list contains the exact string matches to ensure SQL query conditions are accurate. By following this, you can avoid any mistakes while generating SQL queries

                -column names are ["year","item","quater","value","price_type"]
                -item => Refers to the specific expenditure components of GDP being measured , These components are ["Private final consumption expenditure","Gross fixed capital formation","Change in stock","Discrepancies","Valuables","Gross domestic product","Government final consumption expenditure","Less: Imports of goods and services","Exports of goods and services"]
                -quater => Indicates the specific quarter for which the data is reported , can be ["Q1","Q2","Q3","Q4"]
                -value => Refers to the total value of output (in ₹ crore) for each sector in the specified quarter,
                -price_type =>  can be ["Current Price","Constant Price"]
                -year => ["2019-20","2017-18","2011-12","2023-24","2021-22","2012-13","2020-21","2016-17","2014-15","2018-19","2015-16","2013-14","2022-23"]

                IMPORTANT  STRICT RULES:
                When writing the SQL, you MUST use the exact strings copied character-by-character from the given list for the item column.
                Most important: Avoid deeply nested JSON. Keep any lists or dictionaries shallow (max one level).
                Provide all the fields values in thein the output json.
                If value is "0" => convert it to "NA"

                Use this table when:
                -A query mentions a specific quarter, like “Q1 of 2023-24”.
                -You need to analyze short-term trends in GDP components.
                -Comparing seasonal or quarterly variations.
                -You’re evaluating policy impact in a specific quarter.
                -Query requires quarterly GDP, quarter-wise consumption, or investment patterns.
                """,
        "quaterly_estimates_of_gdp": """
                DATA SOURCE => MoSPI

                This table provides quarterly estimates of GDP components, such as: Agriculture, Manufacturing, Services, etc.Growth rates for these sectors during each quarter.
                Important => When setting conditions for column values, always refer to the  list given along with column information. This list contains the exact string matches to ensure SQL query conditions are accurate. By following this, you can avoid any mistakes while generating SQL queries

                -column names are ["year","item","quater","value","price_type"]
                -item => Refers to the specific component of GDP being measured. These components are ["Trade, Hotels, Transport, Communication & Services related to Broadcasting","Agriculture, Livestock, Forestry & Fishing","Manufacturing","GFCF","Construction","PFCE","Public Administration, Defence & Other Services","GFCE","Tertiary Sector","Exports of goods and services","GVA at Basic Prices","Electricity, Gas, Water Supply & Other Utility Services","CIS","Imports of goods and services","Valuables","GDP ","Financial, Real Estate & Professional Services","Mining & Quarrying","Discrepancies* ","Secondary Sector","Primary Sector"].
                -quater => Indicates the specific quarter for which the data is reported , can be ["Q1","Q2","Q3","Q4"]
                -growth_value  => Represents the growth rate of each item during the respective quarter.
                -price_type => ["constant price","current price"]
                -value => Refers to the total value of output (in ₹ crore) for each sector in the specified quarter.
                -year => ["2016-17","2014-15","2018-19","2013-14","2024-25","2022-23","2017-18","2011-12","2021-22","2012-13","2020-21","2015-16","2019-20","2023-24"]

                IMPORTANT STRICT RULES:
                When writing the SQL, you MUST use the exact strings copied character-by-character from the given list for the item column.
                Most important: Avoid deeply nested JSON. Keep any lists or dictionaries shallow (max one level).
                Provide all the fields values in the in the output json.
                If "value" is 0 => convert it to "NA"
                        
                Use this table when:
                -You need to analyze the economic performance of specific GDP sectors in a particular quarter.
                -You are interested in understanding the growth trends for each sector.
                -You need to compare seasonal effects or trends for sectors like agriculture, manufacturing, or services.
                -The analysis involves comparing quarterly fluctuations across years or sectors.
                -You are conducting an economic performance review for specific quarters (e.g., Q2 of 2021-22).

                =>Handling "year" column:
                a.Format of years columns are like this : "2023-24","2019-20","2011-12" etc.... 
                b.so when asked query for a year, for example 2023 you take it like 2023-24 always.
                c.Also make sure when error comes in years column you check the schema and few rows of the tables to know the format.
                d.Dont give id column of the tables in the json response.
                e.Always try navigate the unique values in the columns so that you choose the most relevant table and give correct result.
                f.Always check if the user query includes a specific year. If not, automatically use the latest current available year from the dataset.
                """,
        "none_of_these": """This query does not relate to any of the files present in the database. IMPORTANT: Return a valid JSON with the message "Data is not present." """
    }
    try:
        print("Attempting to find: " + selected_file)
        return description[selected_file]
    except:
        return "I did not find this file in my list of task descriptions."
    
def task_descriptions_by_file_IIP(selected_file):
    selected_file = selected_file.strip()
    description = {
        "iip_annual_data":"""
                column names are => ["year" ,"sector_type","category","sub_category","iip_index","iip_growth_rate","data_source" ,"data_release_date","data_updated_date]
                -Important 1 !!!==> When setting conditions for column values, always take help from the column-wise keywords for iip_annual_data table. This list contains the exact string matches to ensure SQL query conditions are accurate. By following this, you can avoid any mistakes while generating SQL queries.
                year => ["2017-18","2019-20","2021-22","2023-24","2012-13","2014-15","2016-17","2020-21","2013-14","2015-16","2018-19","2022-23"]
                sector_type => ["Sectoral" ,"General" ,"Use-based category"]
                category => ["Intermediate Goods" , "Mining","Consumer Non-durables","Primary Goods","Manufacturing","Infrastructure/ Construction Goods","Capital Goods","General","Consumer Durables","Electricity"] => keep default query condition as "General"  until specified
                sub_category =>[ "*","Manufacture of Furniture","Manufacture of Basic Metals","Manufacture of Electrical Equipment","Manufacture of Motor Vehicles, Trailers and Semi-trailers","Other Manufacturing","Manufacture of Machinery and Equipment N.e.c.","Manufacture of Computer, Electronic and Optical Products","Manufacture of Tobacco Products","Manufacture of Fabricated Metal Products, Except Machinery and Equipment","Manufacture of Chemicals and Chemical Products","*","Printing and Reproduction of Recorded Media","Manufacture of Wearing Apparel","Manufacture of Pharmaceuticals, Medicinal Chemical and Botanical Products","Manufacture of Other Transport Equipment","Manufacture of Textiles","Manufacture of Wood and Products of Wood and Cork, Except Furniture; Manufacture of Articles of Straw and Plaiting Materials","Manufacture of Beverages","Manufacture of Leather and Related Products","Manufacture of Food Products","Manufacture of Coke and Refined Petroleum Products","Manufacture of Rubber and Plastics Products","Manufacture of Paper and Paper Products","Manufacture of Other Non-metallic Mineral Products"] 
                iip_index => is the iip index value for that category/sub_category in that sector.
                iip_growth_rate => is the growth rate/percentage for that category/sub_category in that sector.
                data_source => is the source from where data comes. (In json you must include this field)
                data_release_date => date on which data was released.(In json you must include this field)
                data_updated_date => date on which data was updated.(In json you must include this field)
                Note: you must include  all the  fields in json. 

                -Important 2 !!!==>year column in iip_annual_data table has values in the format of "2015-16","2016-17","2014-15","2012-13" ,"2018-19" etc...
                *So make sure when you generate sql squery you use this format of year  only to get the data.
                *Also, make sure data should be present in the database for the year you are querying for.
                *iip_annual_data table contains data from year 2011-12 to 2023-24 only, so if user query requires data for other years then you should inform user about this.
                *E.g: what is the iip index for last three years? Should answe genral iip index for latest three years in the database.
                """,
        "iip_monthly_data": """
                column names are => ["year" ,"sector_type","category","sub_category","iip_index","iip_growth_rate","data_source" ,"data_release_date","data_updated_date"]
                -Important 1 !!!==> When setting conditions for column values, always take help from the column-wise keywords for iip_monthly_data table. This list contains the exact string matches to ensure SQL query conditions are accurate. By following this, you can avoid any mistakes while generating SQL queries.
                year => ["2013","2014","2016","2015","2024","2019","2025","2012","2023","2022","2017","2018","2020","2021"]
                month => ["June","November","March","August","December","July","January","April","May","February","September","October",]
                sector_type => ["Sectoral" ,"General" ,"Use-based category"]
                category => ["Intermediate Goods" , "Mining","Consumer Non-durables","Primary Goods","Manufacturing","Infrastructure/ Construction Goods","Capital Goods","General","Consumer Durables","Electricity"] => keep default query condition as "General" until specified.
                sub_category => ["*","Manufacture of Furniture","Manufacture of Basic Metals","Manufacture of Electrical Equipment","Manufacture of Motor Vehicles, Trailers and Semi-trailers","Other Manufacturing","Manufacture of Machinery and Equipment N.e.c.","Manufacture of Computer, Electronic and Optical Products","Manufacture of Tobacco Products","Manufacture of Fabricated Metal Products, Except Machinery and Equipment","Manufacture of Chemicals and Chemical Products","*","Printing and Reproduction of Recorded Media","Manufacture of Wearing Apparel","Manufacture of Pharmaceuticals, Medicinal Chemical and Botanical Products","Manufacture of Other Transport Equipment","Manufacture of Textiles","Manufacture of Wood and Products of Wood and Cork, Except Furniture; Manufacture of Articles of Straw and Plaiting Materials","Manufacture of Beverages","Manufacture of Leather and Related Products","Manufacture of Food Products","Manufacture of Coke and Refined Petroleum Products","Manufacture of Rubber and Plastics Products","Manufacture of Paper and Paper Products","Manufacture of Other Non-metallic Mineral Products"]
                iip_index => is the iip index value for that category/sub_category in that sector.
                iip_growth_rate => is the growth rate/percentage for that category/sub_category in that sector.
                data_source => is the source from where data comes. (In json you must include this field)
                data_release_date => date on which data was released.(In json you must include this field)
                Note: you must include all the  fields in json. 
                """,
        "none_of_these": """This query does not relate to any of the files present in the database. IMPORTANT: Return a valid JSON with the message "Data is not present." """}
    try:
        print("Attempting to find: " + selected_file)
        return description[selected_file]
    except:
        return "I did not find this file in my list of task descriptions."

def task_descriptions_by_file_MSME(selected_file):
    selected_file = selected_file.strip()
    description = {"bdi(1)": """for credit growth analysis. "columns": ["year", "month", "sector", "growth_rate_yoy", "previous_year_growth", "remarks"]""",
    "cleaned_adb_asia_sme": """for international MSME comparisons. "columns": ["sector","criteria","micro_threshold","small_threshold","medium_threshold","country"]""",
    "exchange_rate_lcy_usd": """for currency exchange rate analysis. "columns": ["country","2003","2004","2005","2006","2007","2008","2009","2010","2011","2012","2013","2014","2015","2016","2017","2018","2019","2020","2021","2022"]""",
    "gdp_(current_prices)": """for GDP trends. "columns": ["country","2003","2004","2005","2006","2007","2008","2009","2010","2011","2012","2013","2014","2015","2016","2017","2018","2019","2020","2021","2022"]""",
    "state_wise_udyam_registration": """for MSME , Udyam registrations and micro ,small , medium sector registeration by state.  "columns": ["s__no_", "state/ut_name", "total_msmes","total_udyam","imes_(uap)","micro","small","medium"]""",
    "a2._msmes_to_total": """for the percentage of MSMEs among all enterprises by country . "columns": ["country","2003","2004","2005","2006","2007","2008","2009","2010","2011","2012","2013","2014","2015","2016","2017","2018","2019","2020","2021","2022"]""",
    "a3._msmes_by_sector": """for sectoral distribution of MSMEs (latest year available) . "columns": ["item","philippines","azerbaijan","georgia","kazakhstan","brunei_darussalam","lao_people’s_democratic_republic","uzbekistan","pakistan","viet_nam","samoa","sri_lanka","armenia","kyrgyz_republic","tajikistan","fiji","papua_new_guinea","nepal*","cambodia","indonesia","malaysia","myanmar","singapore","thailand","bangladesh","india*"]""",
    "a4._msmes_by_region": """for  regional distribution of MSMEs within countries (latest year). "columns": ["item","sri_lanka","armenia","azerbaijan","georgia","kazakhstan","kyrgyz_republic","tajikistan","uzbekistan","lao_people’s_democratic_republic","thailand","malaysia","bangladesh","cambodia","philippines","pakistan","samoa","brunei_darussalam","indonesia","myanmar*","singapore","viet_nam","india*","nepal*","fiji","papua_new_guinea"]""",
    "a5._number_of_employees_by_msmes": """for employment numbers in MSMEs over time by country. "columns": ["country","2003","2004","2005","2006","2007","2008","2009","2010","2011","2012","2013","2014","2015","2016","2017","2018","2019","2020","2021","2022"]""",
    "a6._msme_employees_to_total": """for the percentage of total employment represented by MSMEs. "columns": ["country","2003","2004","2005","2006","2007","2008","2009","2010","2011","2012","2013","2014","2015","2016","2017","2018","2019","2020","2021","2022"]""",
    "a7._msme_employees_by_sector": """for which sectors employ the most MSME workers (latest year). "columns": ["item","georgia","kazakhstan","lao_people’s_democratic_republic","viet_nam","uzbekistan","philippines","brunei_darussalam","azerbaijan","india*","nepal","pakistan*","sri_lanka","armenia","kyrgyz_republic","tajikistan","fiji","papua_new_guinea","samoa","cambodia","indonesia","malaysia","myanmar","singapore","thailand","bangladesh"]""",
    "a8._msme_employees_by_region": """for regional employment share in MSMEs (latest year). "columns": ["item","malaysia","thailand","sri_lanka","armenia","azerbaijan","georgia","kazakhstan","kyrgyz_republic","cambodia","uzbekistan","bangladesh","papua_new_guinea","philippines","samoa","brunei_darussalam","indonesia","lao_people’s_democratic_republic","myanmar","singapore","viet_nam","india*","nepal","pakistan","tajikistan","fiji"]""",
    "a9_1._gdp_of_msmes_(local_currency)": """for GDP contribution of MSMEs in local currencies over time. "columns": ["country","2003","2004","2005","2006","2007","2008","2009","2010","2011","2012","2013","2014","2015","2016","2017","2018","2019","2020","2021","2022","unit:"]""",
    "a9_2._gdp_of_msmes_(million)": """for MSME GDP in USD across countries over time. "columns": "columns": ["country","2003","2004","2005","2006","2007","2008","2009","2010","2011","2012","2013","2014","2015","2016","2017","2018","2019","2020","2021","2022"]""",
    "a10._msme_contribution_to_gdp": """for percentage of GDP generated by MSMEs per country.  "columns": ["country","2003","2004","2005","2006","2007","2008","2009","2010","2011","2012","2013","2014","2015","2016","2017","2018","2019","2020","2021","2022"]""",
    "a11._msme_gdp_by_sector": """for sectors contribute most to MSME GDP (latest year). "columns": ["item","kyrgyz_republic","georgia","cambodia","indonesia","lao_people’s_democratic_republic","malaysia","myanmar","philippines","singapore","thailand","viet_nam","bangladesh","india","nepal","pakistan","sri_lanka","armenia","azerbaijan","kazakhstan","tajikistan","uzbekistan","fiji","papua_new_guinea","samoa","brunei_darussalam" """,
    "a13_1._msme_export_value_(local_currency)": """for MSME export value in local currencies over time. "columns": ["country","2003","2004","2005","2006","2007","2008","2009","2010","2011","2012","2013","2014","2015","2016","2017","2018","2019","2020","2021","2022","unit:" ] """,
    "a13_2._msme_export_value_(million)": """for MSME exports in USD across countries over time.  "columns":["country","2003","2004","2005","2006","2007","2008","2009","2010","2011","2012","2013","2014","2015","2016","2017","2018","2019","2020","2021","2022"]""",
    "a14._msme_exports_to_total": """for the percentage of total exports contributed by MSMEs. "columns": ["country","2003","2004","2005","2006","2007","2008","2009","2010","2011","2012","2013","2014","2015","2016","2017","2018","2019","2020","2021","2022"]""",
    "a1._number_of_msmes": """for total number of MSMEs per country over years. "columns": "columns": ["country","2003","2004","2005","2006","2007","2008","2009","2010","2011","2012","2013","2014","2015","2016","2017","2018","2019","2020","2021","2022"]""",
    "nifty_sme_emerge": """for Nifty SME Emerge related over time contains open, high ,low ,close columns": ["index_name", "date", "open", "high","low","close"]""",
    "none_of_these": """This query does not relate to any of the files present in the database. IMPORTANT: Return a valid JSON with the message "Data is not present." """}
    try:
        print("Attempting to find: " + selected_file)
        return description[selected_file]
    except:
        return "I did not find this file in my list of task descriptions."

