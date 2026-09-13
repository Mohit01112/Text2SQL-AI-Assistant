# ============================================================
# TEXT2SQL AI ASSISTANT
# COMPLETE UPDATED APP.PY
# ============================================================


import os
import re

from decimal import Decimal
from datetime import datetime, date

from flask import (
    Flask,
    render_template,
    request,
    jsonify
)

from dotenv import load_dotenv

from sqlalchemy import (
    create_engine,
    text,
    inspect
)

from langchain_community.utilities import SQLDatabase

from langchain_community.vectorstores import FAISS

from langchain_huggingface import HuggingFaceEmbeddings

from langchain_groq import ChatGroq


# ============================================================
# LOAD ENVIRONMENT VARIABLES
# ============================================================

load_dotenv()


# ============================================================
# FLASK APPLICATION
# ============================================================

app = Flask(__name__)


# ============================================================
# DATABASE CONFIGURATION
# ============================================================

DB_HOST = os.getenv(
    "DB_HOST",
    "localhost"
)

DB_PORT = os.getenv(
    "DB_PORT",
    "3306"
)

DB_USERNAME = os.getenv(
    "DB_USERNAME"
)

DB_PASSWORD = os.getenv(
    "DB_PASSWORD"
)

DB_NAME = os.getenv(
    "DB_NAME"
)

GROQ_API_KEY = os.getenv(
    "GROQ_API_KEY"
)


# ============================================================
# CHECK REQUIRED ENVIRONMENT VARIABLES
# ============================================================

missing_variables = []


if not DB_USERNAME:

    missing_variables.append(
        "DB_USERNAME"
    )


if DB_PASSWORD is None:

    missing_variables.append(
        "DB_PASSWORD"
    )


if not DB_NAME:

    missing_variables.append(
        "DB_NAME"
    )


if not GROQ_API_KEY:

    missing_variables.append(
        "GROQ_API_KEY"
    )


if missing_variables:

    print("\n")

    print("=" * 60)

    print(
        "ERROR: Missing environment variables:"
    )

    print()

    for variable in missing_variables:

        print(
            f"- {variable}"
        )

    print()

    print(
        "Please check your .env file."
    )

    print("=" * 60)

    print()

    raise ValueError(
        "Missing required environment variables."
    )


# ============================================================
# CREATE MYSQL CONNECTION
# ============================================================

MYSQL_URI = (

    f"mysql+pymysql://"

    f"{DB_USERNAME}:"

    f"{DB_PASSWORD}@"

    f"{DB_HOST}:"

    f"{DB_PORT}/"

    f"{DB_NAME}"

)


engine = create_engine(

    MYSQL_URI,

    pool_pre_ping=True,

    pool_recycle=3600

)


# ============================================================
# LANGCHAIN SQL DATABASE
# ============================================================

db = SQLDatabase.from_uri(

    MYSQL_URI

)


# ============================================================
# INITIALIZE GROQ LLM
# ============================================================

llm = ChatGroq(

    groq_api_key=GROQ_API_KEY,

    model=os.getenv(
        "GROQ_MODEL",
        "openai/gpt-oss-20b"
    ),

    temperature=0

)


# ============================================================
# HUGGINGFACE EMBEDDINGS
# ============================================================

print("\nLoading HuggingFace embeddings...")


embeddings = HuggingFaceEmbeddings(

    model_name=

    "sentence-transformers/all-MiniLM-L6-v2"

)


print(
    "Embeddings loaded successfully."
)


# ============================================================
# ANALYZE DATABASE
# ============================================================

print("\n")

print("=" * 60)

print(
    "ANALYZING DATABASE..."
)

print("=" * 60)


# ============================================================
# BUILD DATABASE KNOWLEDGE
# ============================================================

def build_database_knowledge():

    inspector = inspect(
        engine
    )


    tables = inspector.get_table_names()


    documents = []


    relationships = []


    print(
        "\nAVAILABLE TABLES:"
    )


    for table in tables:

        print(
            f"- {table}"
        )


    # ========================================================
    # TABLE SCHEMA
    # ========================================================

    for table in tables:


        columns = inspector.get_columns(
            table
        )


        primary_keys = inspector.get_pk_constraint(
            table
        )


        foreign_keys = inspector.get_foreign_keys(
            table
        )


        table_information = (

            f"\nTABLE: `{table}`\n"

        )


        table_information += (

            "COLUMNS:\n"

        )


        for column in columns:


            column_name = column[
                "name"
            ]


            column_type = str(

                column[
                    "type"
                ]

            )


            table_information += (

                f"- `{column_name}` "

                f"({column_type})\n"

            )


        # ====================================================
        # PRIMARY KEY
        # ====================================================

        primary_key_columns = (

            primary_keys.get(

                "constrained_columns",

                []

            )

        )


        if primary_key_columns:


            table_information += (

                "\nPRIMARY KEY:\n"

            )


            for primary_key in primary_key_columns:


                table_information += (

                    f"- `{primary_key}`\n"

                )


        # ====================================================
        # FOREIGN KEYS
        # ====================================================

        if foreign_keys:


            table_information += (

                "\nFOREIGN KEYS:\n"

            )


            for foreign_key in foreign_keys:


                local_columns = (

                    foreign_key.get(

                        "constrained_columns",

                        []

                    )

                )


                referenced_table = (

                    foreign_key.get(

                        "referred_table",

                        ""

                    )

                )


                referenced_columns = (

                    foreign_key.get(

                        "referred_columns",

                        []

                    )

                )


                for index in range(

                    len(local_columns)

                ):


                    if index < len(

                        referenced_columns

                    ):


                        relationship = (

                            f"`{table}`."

                            f"`{local_columns[index]}` "

                            f"-> "

                            f"`{referenced_table}`."

                            f"`{referenced_columns[index]}`"

                        )


                        relationships.append(

                            relationship

                        )


                        table_information += (

                            f"- {relationship}\n"

                        )


        documents.append(

            table_information

        )


    # ========================================================
    # INFERRED RELATIONSHIPS
    # ========================================================

    inferred_relationships = []


    table_columns = {}


    for table in tables:


        columns = inspector.get_columns(
            table
        )


        table_columns[table] = [


            column["name"]

            for column in columns


        ]


    # ========================================================
    # FIND SAME COLUMN NAMES
    # ========================================================

    for table_1 in tables:


        for table_2 in tables:


            if table_1 >= table_2:

                continue


            columns_1 = (

                table_columns[table_1]

            )


            columns_2 = (

                table_columns[table_2]

            )


            common_columns = (

                set(columns_1)

                .intersection(

                    set(columns_2)

                )

            )


            for column in common_columns:


                relationship = (

                    f"`{table_1}`."

                    f"`{column}` "

                    f"<-> "

                    f"`{table_2}`."

                    f"`{column}`"

                    f" [INFERRED]"

                )


                inferred_relationships.append(

                    relationship

                )


    # ========================================================
    # CUSTOM RELATIONSHIP DETECTION
    # ========================================================

    custom_relationship_candidates = [


        (
            "2017_budgets",
            "Product Name",
            "products",
            "Product Name"
        ),


        (
            "sales_order",
            "Product Description Index",
            "products",
            "Index"
        ),


        (
            "sales_order",
            "Delivery Region Index",
            "regions",
            "id"
        ),


        (
            "sales_order",
            "Customer Index",
            "customers",
            "Index"
        ),


        (
            "regions",
            "state_code",
            "state_regions",
            "State Code"
        ),


        (
            "regions",
            "state",
            "state_regions",
            "State"
        )

    ]


    for (

        source_table,
        source_column,
        target_table,
        target_column

    ) in custom_relationship_candidates:


        if (

            source_table

            in table_columns

            and

            target_table

            in table_columns

        ):


            if (

                source_column

                in table_columns[source_table]

                and

                target_column

                in table_columns[target_table]

            ):


                relationship = (

                    f"`{source_table}`."

                    f"`{source_column}` "

                    f"-> "

                    f"`{target_table}`."

                    f"`{target_column}`"

                    f" [INFERRED]"

                )


                if (

                    relationship

                    not in inferred_relationships

                    and

                    relationship

                    not in relationships

                ):


                    inferred_relationships.append(

                        relationship

                    )


    # ========================================================
    # REMOVE DUPLICATES
    # ========================================================

    all_relationships = []


    for relationship in (

        relationships

        + inferred_relationships

    ):


        if (

            relationship

            not in all_relationships

        ):


            all_relationships.append(

                relationship

            )


    # ========================================================
    # PRINT RELATIONSHIPS
    # ========================================================

    print(
        "\nDETECTED RELATIONSHIPS:"
    )


    if all_relationships:


        for relationship in all_relationships:


            print(
                relationship
            )


    else:


        print(
            "No relationships detected."
        )


    # ========================================================
    # ADD RELATIONSHIPS TO VECTOR DOCUMENTS
    # ========================================================

    relationship_document = (

        "\nDATABASE RELATIONSHIPS:\n\n"

    )


    if all_relationships:


        for relationship in all_relationships:


            relationship_document += (

                f"- {relationship}\n"

            )


    else:


        relationship_document += (

            "No relationships detected.\n"

        )


    documents.append(

        relationship_document

    )


    # ========================================================
    # COMPLETE DATABASE SCHEMA
    # ========================================================

    try:


        complete_schema = (

            db.get_table_info()

        )


        documents.append(

            "COMPLETE DATABASE SCHEMA:\n\n"

            + complete_schema

        )


    except Exception as error:


        print(

            "\nWarning while getting complete schema:"

        )


        print(
            error
        )


    return (

        documents,

        all_relationships

    )


# ============================================================
# BUILD DATABASE KNOWLEDGE
# ============================================================

database_documents, relationships = (

    build_database_knowledge()

)


# ============================================================
# CREATE VECTOR DATABASE
# ============================================================

print(
    "\nCREATING VECTOR DATABASE..."
)


vector_store = FAISS.from_texts(

    database_documents,

    embeddings

)


print(
    "VECTOR DATABASE READY."
)


# ============================================================
# EXTRACT TEXT FROM LLM RESPONSE
# ============================================================

def extract_text(response):


    # ========================================================
    # LANGCHAIN AI MESSAGE
    # ========================================================

    if hasattr(

        response,

        "content"

    ):


        return extract_text(

            response.content

        )


    # ========================================================
    # STRING
    # ========================================================

    if isinstance(

        response,

        str

    ):


        return response.strip()


    # ========================================================
    # DICTIONARY
    # ========================================================

    if isinstance(

        response,

        dict

    ):


        if (

            "text"

            in response

        ):


            return str(

                response["text"]

            ).strip()


        if (

            "content"

            in response

        ):


            return extract_text(

                response["content"]

            )


        return str(

            response

        ).strip()


    # ========================================================
    # LIST
    # ========================================================

    if isinstance(

        response,

        list

    ):


        text_parts = []


        for item in response:


            if isinstance(

                item,

                dict

            ):


                if (

                    item.get("type")

                    == "text"

                ):


                    text_parts.append(

                        str(

                            item.get(

                                "text",

                                ""

                            )

                        )

                    )


                elif (

                    "text"

                    in item

                ):


                    text_parts.append(

                        str(

                            item["text"]

                        )

                    )


                elif (

                    "content"

                    in item

                ):


                    text_parts.append(

                        extract_text(

                            item["content"]

                        )

                    )


            else:


                text_parts.append(

                    extract_text(item)

                )


        return "".join(

            text_parts

        ).strip()


    # ========================================================
    # OTHER
    # ========================================================

    return str(

        response

    ).strip()


# ============================================================
# QUESTION CLASSIFICATION
# ============================================================

def classify_question(question):


    prompt = f"""

You are a classifier for a Text-to-SQL AI Assistant.

Classify the user message into exactly one category:

DATABASE

or

GENERIC


DATABASE means:

The user is asking something that requires
information from a database.

Examples:

What are all products?

Show all customers.

Which product has the highest sales?

What is the budget of Product 12?

Show sales by region.

Which customer has the highest sales?

Compare budget and sales.

How many products are available?

Which product sells the most?


GENERIC means:

Greeting or normal conversation that does not
require database information.

Examples:

Hello

Hi

How are you?

Who are you?

Thank you

Bye


IMPORTANT:

If the user says a greeting AND asks a database
question, return DATABASE.

Example:

Hello, show all products.

Answer:

DATABASE


USER MESSAGE:

{question}


CATEGORY:

"""


    response = llm.invoke(

        prompt

    )


    category = extract_text(

        response

    ).upper()


    print(
        "\nQUESTION TYPE:"
    )


    print(
        category
    )


    if (

        "DATABASE"

        in category

    ):


        return "DATABASE"


    return "GENERIC"


# ============================================================
# GENERATE GENERIC RESPONSE
# ============================================================

def generate_generic_response(question):


    prompt = f"""

You are a friendly AI assistant named
Text2SQL AI Assistant.

The user said:

"{question}"


Your main purpose is to help users interact
with their MySQL database using natural language.


RULES:

1. Respond naturally.

2. Be friendly and professional.

3. Keep the response short.

4. Do not generate SQL.

5. Do not pretend to query the database.

6. If the user says hello or hi,
   greet them and briefly mention that they can
   ask questions about their database.

7. If the user asks how you are,
   respond naturally.

8. If the user asks who you are,
   explain that you are a Text-to-SQL AI Assistant.

9. If the user says thank you,
   respond politely.

10. If the user says bye,
    say goodbye politely.


ANSWER:

"""


    response = llm.invoke(

        prompt

    )


    return extract_text(

        response

    )


# ============================================================
# CLEAN SQL QUERY
# IMPORTANT:
# THIS VERSION PRESERVES WITH / CTE QUERIES
# ============================================================

def clean_sql_query(response):


    query = extract_text(

        response

    )


    query = query.strip()


    # ========================================================
    # REMOVE MARKDOWN BLOCKS
    # ========================================================

    query = re.sub(

        r"```sql",

        "",

        query,

        flags=re.IGNORECASE

    )


    query = re.sub(

        r"```",

        "",

        query

    )


    query = query.strip()


    # ========================================================
    # REMOVE COMMON PREFIXES
    # ========================================================

    prefixes = [


        "SQL QUERY:",

        "SQL:",

        "QUERY:",

        "GENERATED SQL:",

        "MYSQL QUERY:"


    ]


    for prefix in prefixes:


        if query.upper().startswith(

            prefix.upper()

        ):


            query = query[

                len(prefix):

            ].strip()


    # ========================================================
    # FIND START OF SQL
    #
    # IMPORTANT:
    # CHECK WITH FIRST
    # ========================================================

    with_match = re.search(

        r"\bWITH\b",

        query,

        flags=re.IGNORECASE

    )


    select_match = re.search(

        r"\bSELECT\b",

        query,

        flags=re.IGNORECASE

    )


    # ========================================================
    # PRESERVE COMPLETE CTE
    # ========================================================

    if with_match:


        query = query[

            with_match.start():

        ]


    elif select_match:


        query = query[

            select_match.start():

        ]


    else:


        return ""


    # ========================================================
    # REMOVE TEXT AFTER SQL
    #
    # DO NOT SPLIT CTE QUERY INCORRECTLY
    # ========================================================

    query = query.strip()


    # If model returns a semicolon,
    # keep only the first SQL statement.

    if ";" in query:


        first_query = query.split(

            ";",

            1

        )[0].strip()


        if first_query:


            query = first_query


    # ========================================================
    # REMOVE TRAILING SEMICOLON
    # ========================================================

    query = query.rstrip(

        ";"

    ).strip()


    return query


# ============================================================
# FIX COMMON CTE PROBLEMS
# ============================================================

def fix_cte_query(sql_query):


    if not sql_query:


        return sql_query


    query = sql_query.strip()


    query_upper = query.upper()


    # ========================================================
    # IF QUERY STARTS WITH:
    #
    # product_qty AS (
    #
    # BUT DOES NOT START WITH WITH
    # ========================================================

    if (

        not query_upper.startswith(

            "WITH"

        )

        and

        re.match(

            r"^[A-Za-z_][A-Za-z0-9_]*\s+AS\s*\(",

            query,

            flags=re.IGNORECASE

        )

    ):


        query = (

            "WITH "

            + query

        )


    # ========================================================
    # BROKEN CASE:
    #
    # SELECT ...
    # ),
    # ranked AS (
    #
    # THIS USUALLY MEANS THE FIRST CTE WAS REMOVED.
    #
    # WE DO NOT TRY TO GUESS THE MISSING CTE NAME.
    # ========================================================

    if (

        not query.upper().startswith(

            "WITH"

        )

        and

        re.search(

            r"\)\s*,\s*[A-Za-z_][A-Za-z0-9_]*\s+AS\s*\(",

            query,

            flags=re.IGNORECASE

        )

    ):


        return query


    return query


# ============================================================
# VALIDATE SQL QUERY
# ============================================================

def validate_sql_query(sql_query):


    if not sql_query:


        return (

            False,

            "Empty SQL query."

        )


    query = sql_query.strip()


    query_upper = query.upper()


    # ========================================================
    # QUERY MUST START WITH SELECT OR WITH
    # ========================================================

    if not (

        query_upper.startswith(

            "SELECT"

        )

        or

        query_upper.startswith(

            "WITH"

        )

    ):


        return (

            False,

            "Query must start with SELECT or WITH."

        )


    # ========================================================
    # FORBIDDEN KEYWORDS
    # ========================================================

    dangerous_keywords = [


        "INSERT",

        "UPDATE",

        "DELETE",

        "DROP",

        "ALTER",

        "CREATE",

        "TRUNCATE",

        "REPLACE",

        "GRANT",

        "REVOKE",

        "CALL",

        "EXEC",

        "EXECUTE",

        "SET",

        "USE",

        "LOAD",

        "INTO OUTFILE",

        "INTO DUMPFILE"


    ]


    for keyword in dangerous_keywords:


        if re.search(

            rf"\b{re.escape(keyword)}\b",

            query_upper

        ):


            return (

                False,

                f"Unsafe SQL keyword detected: {keyword}"

            )


    # ========================================================
    # BLOCK MULTIPLE SQL STATEMENTS
    # ========================================================

    query_without_final_semicolon = (

        query.rstrip(

            ";"

        )

    )


    if ";" in query_without_final_semicolon:


        return (

            False,

            "Multiple SQL statements are not allowed."

        )


    # ========================================================
    # BASIC BROKEN CTE DETECTION
    # ========================================================

    if (

        not query_upper.startswith(

            "WITH"

        )

        and

        re.search(

            r"\)\s*,\s*[A-Za-z_][A-Za-z0-9_]*\s+AS\s*\(",

            query,

            flags=re.IGNORECASE

        )

    ):


        return (

            False,

            "Invalid CTE query detected. Missing WITH clause."

        )


    return (

        True,

        "Valid SQL query."

    )


# ============================================================
# RETRIEVE RELEVANT DATABASE CONTEXT
# ============================================================

def retrieve_database_context(question):


    relevant_documents = (

        vector_store.similarity_search(

            question,

            k=6

        )

    )


    context_parts = []


    for document in relevant_documents:


        context_parts.append(

            document.page_content

        )


    context = "\n\n".join(

        context_parts

    )


    # ========================================================
    # ADD ALL RELATIONSHIPS
    # ========================================================

    if relationships:


        relationship_context = (

            "\n\nIMPORTANT DATABASE RELATIONSHIPS:\n"

        )


        for relationship in relationships:


            relationship_context += (

                f"- {relationship}\n"

            )


        context += (

            relationship_context

        )


    return context


# ============================================================
# GENERATE SQL QUERY
# ============================================================

def generate_sql_query(question):


    relevant_context = (

        retrieve_database_context(

            question

        )

    )


    sql_prompt = f"""

You are an expert MySQL Text-to-SQL AI system.

Your task is to convert the user's natural language question
into ONE correct executable MySQL SQL query.

You MUST use ONLY the database schema and relationships
provided below.


============================================================

DATABASE CONTEXT:

{relevant_context}


============================================================

USER QUESTION:

{question}


============================================================

IMPORTANT RULES:

1. Generate ONLY the SQL query.

2. Do NOT explain the query.

3. Do NOT use Markdown.

4. Do NOT use triple backticks.

5. Generate ONLY SELECT queries.

6. CTEs are allowed.

7. If using a CTE, the query MUST begin with WITH.

8. A correct CTE query looks exactly like:

WITH product_sales AS (
    SELECT ...
),
ranked AS (
    SELECT ...
)
SELECT ...
FROM ranked

9. NEVER generate:

product_sales AS (...)

without WITH.

10. NEVER generate:

SELECT ...
),
ranked AS (...)

This is invalid SQL.

11. If using multiple CTEs, start the query with:

WITH first_cte AS (...),
second_cte AS (...)
SELECT ...

12. Never generate INSERT.

13. Never generate UPDATE.

14. Never generate DELETE.

15. Never generate DROP.

16. Never generate ALTER.

17. Never generate CREATE.

18. Never generate TRUNCATE.

19. Never invent table names.

20. Never invent column names.

21. Use ONLY tables listed in the database context.

22. Use ONLY columns listed in the database context.

23. When joining tables, use the provided relationships.

24. Use correct MySQL syntax.

25. Use backticks around column names containing spaces.

26. Use table aliases when multiple tables are used.

27. For best-selling product, carefully determine
the requested metric.

If the question asks about quantity or units sold,
use:

SUM(`Order Quantity`)

If the question asks about sales value or revenue,
use the appropriate sales value column available
in the schema.

28. For "top N products in each region",
you may use:

ROW_NUMBER() OVER (
    PARTITION BY region
    ORDER BY metric DESC
)

29. Return ONLY ONE executable SQL query.

30. Before returning the query, verify that all
parentheses are correctly matched.

31. Before returning a CTE query, verify that
the first word is WITH.


SQL QUERY:

"""


    response = llm.invoke(

        sql_prompt

    )


    sql_query = clean_sql_query(

        response

    )


    sql_query = fix_cte_query(

        sql_query

    )


    return sql_query


# ============================================================
# CONVERT DATABASE VALUES
# ============================================================

def convert_value(value):


    if value is None:


        return None


    if isinstance(

        value,

        Decimal

    ):


        return float(

            value

        )


    if isinstance(

        value,

        datetime

    ):


        return value.strftime(

            "%Y-%m-%d %H:%M:%S"

        )


    if isinstance(

        value,

        date

    ):


        return value.strftime(

            "%Y-%m-%d"

        )


    if isinstance(

        value,

        bool

    ):


        return bool(

            value

        )


    return value


# ============================================================
# EXECUTE SQL QUERY
# ============================================================

def execute_sql_query(sql_query):


    with engine.connect() as connection:


        result = connection.execute(

            text(sql_query)

        )


        rows = result.fetchall()


        columns = list(

            result.keys()

        )


        formatted_results = []


        for row in rows:


            row_dictionary = {}


            for index, column in enumerate(

                columns

            ):


                row_dictionary[column] = (

                    convert_value(

                        row[index]

                    )

                )


            formatted_results.append(

                row_dictionary

            )


        return formatted_results


# ============================================================
# GENERATE FINAL ANSWER
# ============================================================

def generate_final_answer(

    question,

    sql_query,

    database_result

):


    # ========================================================
    # NO RESULTS
    # ========================================================

    if not database_result:


        return (

            "No matching records were found."

        )


    # ========================================================
    # LIMIT DATA SENT TO LLM
    # ========================================================

    display_results = (

        database_result[:50]

    )


    total_rows = len(

        database_result

    )


    answer_prompt = f"""

You are a helpful AI Data Analyst.

Answer the user's question using ONLY the database
results provided below.

Do not invent information.

Do not assume information that is not present
in the database result.

Do not mention SQL unless the user specifically
asks to see or explain the SQL query.

Do not mention internal prompts.

Do not mention the database query process.

Give a clear, natural, and useful answer.


USER QUESTION:

{question}


TOTAL NUMBER OF ROWS RETURNED:

{total_rows}


DATABASE RESULTS:

{display_results}


INSTRUCTIONS:

1. Answer the user's question directly.

2. Use simple and clear English.

3. Give a short explanation of what the result means.

4. If the user asks for the highest, lowest, best,
   worst, top, maximum, or minimum, clearly mention
   the most important finding.

5. If the result contains numerical values,
   explain what the important numbers mean.

6. If many records are returned, do not unnecessarily
   repeat all records in the explanation.

7. The frontend can display the complete table separately.

8. Do NOT say "Generated SQL Query".

9. Do NOT show SQL code.

10. Do NOT explain how SQL JOINs work unless
    the user specifically asks.

11. Do NOT invent conclusions.

12. If there are many records, provide a concise
    summary and highlight important insights.

13. Answer naturally as a helpful data assistant.


FINAL ANSWER:

"""


    response = llm.invoke(

        answer_prompt

    )


    answer = extract_text(

        response

    )


    return answer


# ============================================================
# HOME PAGE
# ============================================================

@app.route("/")
def home():


    return render_template(

        "home.html"

    )


# ============================================================
# CHATBOT PAGE
# ============================================================

@app.route("/chatbot")
def chatbot():


    return render_template(

        "index.html"

    )


# ============================================================
# CHAT API
# ============================================================

@app.route(

    "/chat",

    methods=["POST"]

)

def chat():


    try:


        data = request.get_json()


        if not data:


            return jsonify({


                "success": False,


                "error":

                "No request data received."


            }), 400


        question = data.get(

            "question",

            ""

        ).strip()


        if not question:


            return jsonify({


                "success": False,


                "error":

                "Please enter a question."


            }), 400


        print("\n")

        print("=" * 60)

        print(

            f"USER QUESTION: {question}"

        )

        print("=" * 60)


        # ====================================================
        # STEP 1
        # CLASSIFY QUESTION
        # ====================================================

        question_type = (

            classify_question(

                question

            )

        )


        # ====================================================
        # GENERIC QUESTION
        # ====================================================

        if question_type == "GENERIC":


            print(

                "\nPROCESSING GENERIC QUESTION..."

            )


            generic_answer = (

                generate_generic_response(

                    question

                )

            )


            print(

                "\nGENERIC ANSWER:"

            )


            print(

                generic_answer

            )


            return jsonify({


                "success": True,


                "answer":

                generic_answer,


                "results": [],


                "row_count": 0,


                "sql_query": None,


                "type": "generic"


            })


        # ====================================================
        # DATABASE QUESTION
        # ====================================================

        print(

            "\nPROCESSING DATABASE QUESTION..."

        )


        # ====================================================
        # STEP 2
        # GENERATE SQL
        # ====================================================

        sql_query = (

            generate_sql_query(

                question

            )

        )


        print(

            "\nGENERATED SQL:"

        )


        print(

            sql_query

        )


        # ====================================================
        # STEP 3
        # CHECK EMPTY SQL
        # ====================================================

        if not sql_query:


            return jsonify({


                "success": False,


                "error":

                "Unable to generate a SQL query."


            }), 400


        # ====================================================
        # STEP 4
        # VALIDATE SQL
        # ====================================================

        is_valid, message = (

            validate_sql_query(

                sql_query

            )

        )


        if not is_valid:


            print(

                "\nSQL VALIDATION FAILED:"

            )


            print(

                message

            )


            return jsonify({


                "success": False,


                "error":

                message


            }), 400


        # ====================================================
        # STEP 5
        # EXECUTE SQL
        # ====================================================

        print(

            "\nEXECUTING SQL..."

        )


        results = (

            execute_sql_query(

                sql_query

            )

        )


        print(

            f"ROWS RETURNED: {len(results)}"

        )


        # ====================================================
        # STEP 6
        # GENERATE FINAL ANSWER
        # ====================================================

        print(

            "\nGENERATING FINAL ANSWER..."

        )


        final_answer = (

            generate_final_answer(


                question,


                sql_query,


                results


            )

        )


        print(

            "\nFINAL ANSWER:"

        )


        print(

            final_answer

        )


        print("\n")

        print("=" * 60)


        # ====================================================
        # STEP 7
        # RETURN RESPONSE
        # ====================================================

        return jsonify({


            "success": True,


            "answer":

            final_answer,


            "results":

            results,


            "row_count":

            len(results),


            "sql_query":

            sql_query,


            "type":

            "database"


        })


    # ========================================================
    # ERROR HANDLING
    # ========================================================

    except Exception as error:


        print("\n")

        print("=" * 60)

        print(

            "ERROR:"

        )


        print(

            str(error)

        )


        print("=" * 60)


        import traceback


        traceback.print_exc()


        return jsonify({


            "success": False,


            "error":

            str(error)


        }), 500


# ============================================================
# RUN FLASK APPLICATION
# ============================================================

if __name__ == "__main__":


    print("\n")

    print("=" * 60)

    print(

        "TEXT2SQL AI ASSISTANT IS READY"

    )

    print("=" * 60)

    print("\n")


    app.run(


        debug=True,


        host="0.0.0.0",


        port=5000


    )