import os
from autogen import config_list_from_json
import autogen
from dotenv import load_dotenv
import pandas as pd
from langchain_groq import ChatGroq
# from langchain.llms import Llama

# Load environment variables
load_dotenv()

# Set up Llama model
# llm = Llama(model_path="path/to/llama/model")

# llm=ChatGroq(groq_api_key='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',
#              model_name="Llama3-8b-8192")

os.environ["AUTOGEN_USE_DOCKER"] = "False"
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
llm_config = {
    "cache_seed": 48,
    "config_list": [{
        "model": os.environ.get("OPENAI_MODEL_NAME", "llama3-70b-8192"), 
        "api_key": os.environ["GROQ_API_KEY"], 
        "base_url": os.environ.get("OPENAI_API_BASE", "https://api.groq.com/openai/v1")
        }
    ],
}




def write_to_file(filename, message):
    with open(filename, "a") as file:
        file.write(message + "\n")

# Define the "management" group chat:
def management(query):
    ceo = autogen.AssistantAgent(
        name="ceo",
        system_message="You are the CEO of the company. Your role is to analyze the given task, divide it into manageable steps, and provide guidance to the team.",
        llm=llm_config,
    )

    cto = autogen.AssistantAgent(
        name="cto",
        system_message="You are the CTO of the company. Your role is to provide technical insights and recommendations for the task at hand.",
        llm=llm_config,
    )

    coo = autogen.AssistantAgent(
        name="coo",
        system_message="You are the COO of the company. Your role is to ensure smooth operations and resource allocation for the task.",
        llm=llm_config,
    )

    user_proxy = autogen.UserProxyAgent(
        name="User_proxy",
        code_execution_config={"last_n_messages": 2, "work_dir": "coding", "use_docker": False},
        is_termination_msg=lambda x: x.get("content", "") and x.get(
            "content", "").rstrip().endswith("TERMINATE"),
        human_input_mode="TERMINATE",
    )

    groupchat = autogen.GroupChat(
        agents=[user_proxy, ceo, cto, coo],
        messages=[],
        max_round=5)
    manager = autogen.GroupChatManager(groupchat=groupchat)

    filename = "management_conversation.txt"
    write_to_file(filename, f"User: {query}")

    user_proxy.initiate_chat(manager, message=query)

    user_proxy.stop_reply_at_receive(manager)
    user_proxy.send(
        "Give me the goals of the project, number of files that need to be created, and what type of files they are (ex. HTML, CSS, javascript), return ONLY the answer to this message", manager)

    return user_proxy.last_message()["content"]

# Define "code generation" group chat. Receives "guide" and topic
def code_generation(guide, topic):
    coder = autogen.AssistantAgent(
        name="coder",
        system_message="You are the lead coder responsible for generating code based on the provided guidelines and topic.",
        llm=llm_config,
    )

    code_critic = autogen.AssistantAgent(
        name="code_critic",
        system_message="You are the code critic responsible for reviewing and providing feedback on the generated code.",
        llm=llm_config,
    )

    tester = autogen.AssistantAgent(
        name="tester",
        system_message="You are the tester responsible for testing the generated code and ensuring it meets the requirements.",
        llm=llm_config,
    )

    documenter = autogen.AssistantAgent(
        name="documenter",
        system_message="You are the documenter responsible for creating documentation for the generated code.",
        llm=llm_config,
    )

    user_proxy = autogen.UserProxyAgent(
        name="admin",
        system_message="A human admin. Interact with the code generation team to ensure the code meets the requirements.",
        code_execution_config=False,
        is_termination_msg=lambda x: x.get("content", "") and x.get(
            "content", "").rstrip().endswith("TERMINATE"),
        human_input_mode="TERMINATE",
    )

    groupchat = autogen.GroupChat(
        agents=[user_proxy, coder, code_critic, tester, documenter],
        messages=[],
        max_round=5)
    manager = autogen.GroupChatManager(groupchat=groupchat)

    filename = "code_generation_conversation.txt"
    write_to_file(filename, f"User: Write code for {topic} based on the following guidelines: {guide}")

    user_proxy.initiate_chat(
        manager, message=f"Write code for {topic} based on the following guidelines: {guide}")

    user_proxy.stop_reply_at_receive(manager)
    user_proxy.send(
        "Give me the code that was just generated again, return ONLY the code, and add TERMINATE at the end of the message", manager)

    return user_proxy.last_message()["content"]

llm_config_content_assistant = {
    "functions": [
        {
            "name": "management",
            "description": "Analyze and divide the given task. Create bullet points to divide the task into various steps.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The task to be analyzed and divided.",
                    }
                },
                "required": ["query"],
            },
        },
        {
            "name": "code_generation",
            "description": "Write code that accomplishes the given task.",
            "parameters": {
                "type": "object",
                "properties": {
                    "guide": {
                        "type": "string",
                        "description": "Guide that details what needs to be created and how it will be created. Be very specific. Combine the conversation from management function.",
                    },
                    "topic": {
                        "type": "string",
                        "description": "The topic of the code.",
                    }
                },
                "required": ["guide", "topic"],
            },
        },
    ],
    "llm_config": llm_config}

company01 = autogen.AssistantAgent(
    name="company01",
    system_message="You are the manager of Company01. Your role is to oversee the entire operation, analyze tasks, and generate code. You can use the management function to analyze the given task and divide it into bullet points, and then use the code_generation function to write the code for the task. Reply TERMINATE when your task is done.",
    llm_config=llm_config,
)

user_proxy = autogen.UserProxyAgent(
    name="User_proxy",
    human_input_mode="TERMINATE",
    function_map={
        "management": management,
        "code_generation": code_generation,
    },
    code_execution_config={"use_docker": False}
)

user_proxy.initiate_chat(
    company01, message="Create a full stack blog website for my portfolio.")