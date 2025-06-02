import os
import re
import logging
from dotenv import load_dotenv
import time
from app.extensions import db
from app.assistants.models import Assistant
from app.base_knowledge.models import BaseKnowledge, assistant_base_knowledge

from langchain_core.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq
from langchain.memory import ConversationBufferMemory
from langchain.prompts import (
    ChatPromptTemplate,
    MessagesPlaceholder,
    SystemMessagePromptTemplate,
    HumanMessagePromptTemplate,
)
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain.tools import Tool
from langchain.chains import RetrievalQA
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain_openai import ChatOpenAI
from langchain.tools.retriever import create_retriever_tool

load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class AssistantLLM:
    def __init__(self, assistant_id):
        self.assistant_id = assistant_id
        self.assistant = Assistant.query.get(self.assistant_id)
        
        self.llm = ChatGroq(
            model=self.assistant.llm_model,
            temperature=self.assistant.llm_temperature,
            max_tokens=self.assistant.llm_max_tokens
        )

        self.memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)
        self.embedding_function = OpenAIEmbeddings()
        self.tools = []

        self.get_knowledge_base()
        self.prompt = self.get_prompt()
        

        self.agent = create_tool_calling_agent(self.llm, self.tools, self.prompt)
        self.agent_executor = AgentExecutor(
            agent=self.agent,
            tools=self.tools,
            memory=self.memory,
            verbose=True,
            max_iterations=2  # Limit to 2 iterations per query to avoid repeated tool calls.
        )

    def create_tool_func(self, info_chain):
        """Helper to create a function that calls the corresponding info_chain."""
        def tool_func(query):
            return info_chain({"query": query})
        return tool_func

    def get_knowledge_base(self):
        try:
            base_knowledge = (
                db.session.query(BaseKnowledge)
                .join(assistant_base_knowledge)
                .filter(assistant_base_knowledge.c.assistant_id == self.assistant_id)
                .all()
            )
         
            for knowledge in base_knowledge:
                name = knowledge.name
                path = os.path.join(knowledge.folder_path, 'chroma_db')
                description = knowledge.description

                db_chroma = Chroma(persist_directory=path, embedding_function=self.embedding_function)
                info_chain = RetrievalQA.from_chain_type(
                    llm=self.llm, 
                    chain_type="stuff", 
                    retriever=db_chroma.as_retriever(), 
                    return_source_documents=True,
                    verbose=True
                )
                tool = Tool(
                    name=name,
                    description=f"Use this tool to get information about: {description}",
                    func=self.create_tool_func(info_chain)
                )
                self.tools.append(tool)

        except Exception as e:
            logger.error(f"Error getting knowledge base: {str(e)}")
            return None

        
    def get_prompt(self):
        try:
            if not self.assistant:
                raise ValueError(f"No assistant found with id {self.assistant_id}")
            
            tools_str = "\n".join([
                f"- {tool.name}: {tool.description}" 
                for tool in self.tools
            ])
            
            system_prompt = f"""
            

You are a helpful conversational AI assistant. Your goal is to assist users by providing accurate, concise, and helpful responses.

## Rules
- **Strict Rule Compliance:** Follow these rules precisely. Any violation is not tolerated.

### Tool Usage Guidelines
- Only use a tool if it directly contributes to answering the user's query.
- Limit to one tool call per query. Do not call additional tools afterward.
- Never reveal the tool’s name or internal details in your response.
- After using a tool, incorporate the findings into your response without mentioning the tool.
- Do not invent information; rely on tool outputs or your general knowledge.

### Conversation Style
- Write numbers, dates and times in words.
- Use a conversational tone, as if speaking to a friend.
- Keep responses brief to mimic natural dialogue in phone calls.
- Use casual phrases like "Umm...", "Well...", or "I mean..." to sound more human.
- Avoid unnecessary details or repetition to keep the conversation flowing.
- If you don’t know an answer, simply say so.

### Additional Requirements
- Do not include tool names, descriptions, or technical details in responses.
- Base replies on provided information or general knowledge only.
- Be open to refining your responses based on user feedback to improve accuracy and relevance.

## Tools
You have access to the following tools:  
{tools_str}

## Conversation Prompt
{self.assistant.prompt}

"""

            return ChatPromptTemplate.from_messages([
                ("system", system_prompt),
                MessagesPlaceholder(variable_name="chat_history"),
                ("human", "{input}"),
                ("placeholder", "{agent_scratchpad}")
            ])

        except Exception as e:
            logger.error(f"Error getting prompt: {str(e)}")
            raise

    def clean_response(self, text):
        """Remove function-like patterns from the response."""

        # Remove patterns like <function=name>content</function>
        cleaned_text = re.sub(r'<function=.*?</function>', '', text)
        return cleaned_text

    def get_response(self, text):
        try:
            logger.info(f"Assistant is responding...")
            self.memory.chat_memory.add_user_message(text)
            logger.info(f"Added message to memory: {text}")
            
            response = self.agent_executor.invoke({
                "input": text,
                "chat_history": self.memory.chat_memory.messages
            })
            
            answer = response["output"]
            self.memory.chat_memory.add_ai_message(answer)
            logger.info(f"Added message to memory: {text}")
            
            logger.info(f"Memory: {self.memory.load_memory_variables({})}")
            logger.info(f"Assistant response: {answer}")
            return self.clean_response(answer)

        except Exception as e:
            logger.error(f"Error getting response: {str(e)}")
            return "I apologize, but I encountered an error while processing your request."


if __name__ == "__main__":
    pass
