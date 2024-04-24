import os
from autogen import config_list_from_json
import autogen
from dotenv import load_dotenv
import openai

# Get API key
load_dotenv()
config_list = config_list_from_json(env_or_file="OAI_CONFIG_LIST")
openai.api_key = os.getenv("OPENAI_API_KEY")

def write_to_file(filename, message):
    with open(filename, "a") as file:
        file.write(message + "\n")

# ... (management, front_end, and back_end functions remain the same)
def management(query):
    ceo = autogen.AssistantAgent(
        name="ceo",
        system_message="You are the CEO of the company. Your role is to analyze the given task, divide it into manageable steps, and provide guidance to the team.",
        llm_config={"config_list": config_list},
    )

    cto = autogen.AssistantAgent(
        name="cto",
        system_message="You are the CTO of the company. Your role is to provide technical insights and recommendations for the task at hand.",
        llm_config={"config_list": config_list},
    )

    coo = autogen.AssistantAgent(
        name="coo",
        system_message="You are the COO of the company. Your role is to ensure smooth operations and resource allocation for the task.",
        llm_config={"config_list": config_list},
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
        max_round=4)
    manager = autogen.GroupChatManager(groupchat=groupchat)

    #Save the file to a txt
    filename = "management_conversation.txt"
    write_to_file(filename, f"User: {query}")

    def save_message(agent, message):
        write_to_file(filename, f"{agent.name}: {message}")

    # user_proxy.register_callback(save_message)

    # user_proxy.initiate_chat(manager, message=query)

    user_proxy.initiate_chat(manager, message=query)

    user_proxy.stop_reply_at_receive(manager)
    user_proxy.send(
        "Summarize the conversation: give me the goals of the project, number of files that need to be created, and what type of files they are (ex. HTML, CSS, javascript), return ONLY the answer to this message", manager)

    return user_proxy.last_message()["content"]

def front_end(guide, topic):
    designer = autogen.AssistantAgent(
        name="designer",
        system_message="You are the UI/UX designer responsible for creating the design and layout of the front-end based on the provided guidelines and topic.",
        llm_config={"config_list": config_list},
    )

    frontend_dev = autogen.AssistantAgent(
        name="frontend_dev",
        system_message="You are the html developer responsible for implementing the design and creating the HTML code.",
        llm_config={"config_list": config_list},
    )

    css_dev = autogen.AssistantAgent(
        name="frontend_dev",
        system_message="You are the css developer responsible for implementing the design and creating the CSS code.",
        llm_config={"config_list": config_list},
    )
    js_dev = autogen.AssistantAgent(
        name="frontend_dev",
        system_message="You are the js developer responsible for implementing the design and creating the JavaScript code.",
        llm_config={"config_list": config_list},
    )

    code_critic = autogen.AssistantAgent(
        name="code_critic",
        system_message="You are the code critic responsible for reviewing and providing feedback on the generated code.",
        llm_config={"config_list": config_list},
    )

    tester = autogen.AssistantAgent(
        name="tester",
        system_message="You are the tester responsible for testing the generated code and ensuring it meets the requirements.",
        llm_config={"config_list": config_list},
    )

    user_proxy = autogen.UserProxyAgent(
        name="admin",
        system_message="A human admin. Interact with the front-end team to ensure the design and code meet the requirements.",
        code_execution_config=False,
        is_termination_msg=lambda x: x.get("content", "") and x.get(
            "content", "").rstrip().endswith("TERMINATE"),
        human_input_mode="TERMINATE",
    )

    groupchat = autogen.GroupChat(
        agents=[user_proxy, designer, frontend_dev, code_critic, tester, css_dev, js_dev],
        messages=[],
        max_round=5)
    manager = autogen.GroupChatManager(groupchat=groupchat)

    filename = "frontend_conversation.txt"
    write_to_file(filename, f"User: Create the front-end for {topic} based on the following guidelines: {guide}")

    def save_message(agent, message):
        write_to_file(filename, f"{agent.name}: {message}")

    user_proxy.initiate_chat(
        manager, message=f"Create the front-end for {topic} based on the following guidelines: {guide}")

    user_proxy.stop_reply_at_receive(manager)
    user_proxy.send(
        "Give me the HTML, CSS, and JavaScript code, return ONLY the code, and add TERMINATE at the end of the message", manager)

    return user_proxy.last_message()["content"]

def back_end(guide, topic):
    backend_dev = autogen.AssistantAgent(
        name="backend_dev",
        system_message="You are the back-end developer responsible for designing and implementing the server-side logic and database based on the provided guidelines and topic.",
        llm_config={"config_list": config_list},
    )

    dba = autogen.AssistantAgent(
        name="dba",
        system_message="You are the database administrator responsible for designing and managing the database schema and queries.",
        llm_config={"config_list": config_list},
    )

    user_proxy = autogen.UserProxyAgent(
        name="admin",
        system_message="A human admin. Interact with the back-end team to ensure the server-side logic and database meet the requirements.",
        code_execution_config=False,
        is_termination_msg=lambda x: x.get("content", "") and x.get(
            "content", "").rstrip().endswith("TERMINATE"),
        human_input_mode="TERMINATE",
    )

    groupchat = autogen.GroupChat(
        agents=[user_proxy, backend_dev, dba],
        messages=[],
        max_round=5)
    manager = autogen.GroupChatManager(groupchat=groupchat)

    filename = "backend_conversation.txt"
    write_to_file(filename, f"User: Create the back-end for {topic} based on the following guidelines: {guide}")

    def save_message(agent, message):
        write_to_file(filename, f"{agent.name}: {message}")

    user_proxy.initiate_chat(
        manager, message=f"Create the back-end for {topic} based on the following guidelines: {guide}")

    user_proxy.stop_reply_at_receive(manager)
    user_proxy.send(
        "Give me the server-side code and database queries that were just generated, return ONLY the code, and add TERMINATE at the end of the message", manager)

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
            "name": "front_end",
            "description": "Write the front end code that accomplishes the given task.",
            "parameters": {
                "type": "object",
                "properties": {
                    "guide": {
                        "type": "string",
                        "description": "Guide that details what needs to be created and how it will be created. Be very specific in mentioning the name of the files that need to be created. Combine the conversation from management function.",
                    },
                    "topic": {
                        "type": "string",
                        "description": "The topic of the code.",
                    }
                },
                "required": ["guide", "topic"],
            },
        },
        {
            "name": "back_end",
            "description": "Write back end code that accomplishes the given task.",
            "parameters": {
                "type": "object",
                "properties": {
                    "guide": {
                        "type": "string",
                        "description": "Give the entire front end code. Also give the output from the management function",
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
    "config_list": config_list}

company01 = autogen.AssistantAgent(
    name="company01",
    system_message="You are the manager of Company01. Your role is to oversee the entire operation, analyze tasks, and generate code. First, use the management function to analyze the given task and divide it into bullet points. Then, use the front_end function to write the code for the front end. Finally, use the back_end function to write the code for the back end. The output of the management function should be the input to the front_end function. The output of the management function and the output of the front_end function should be the input to the back_end function. Reply TERMINATE when your task is done.",
    llm_config=llm_config_content_assistant,
    max_consecutive_auto_reply=4,
)

user_proxy = autogen.UserProxyAgent(
    name="User_proxy",
    human_input_mode="TERMINATE",
    function_map={
        "management": management,
        "front_end": front_end,
        "back_end": back_end,
    },
    code_execution_config={"use_docker": False}
)

# Initiate the chat with the task
user_proxy.initiate_chat(
    company01, message="Create a full stack blog website for my portfolio.")

# Get the output of the management function
management_output = user_proxy.last_message()["content"]

# Pass the management output to the front_end function
front_end_output = front_end(management_output, "Blog Website")

# Pass the management output and front_end output to the back_end function
back_end_output = back_end(management_output + "\n" + front_end_output, "Blog Website")

# Write the front_end and back_end outputs to a file
with open("output.txt", "w") as file:
    file.write("Front End Output:\n")
    file.write(front_end_output + "\n\n")
    file.write("Back End Output:\n")
    file.write(back_end_output)