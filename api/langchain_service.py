import ast
from langchain_core.runnables import RunnableWithMessageHistory
from langchain.memory.buffer import ConversationBufferMemory
from langchain_openai import OpenAI
from django.conf import settings
from .models import ChatHistory


def get_conversation_chain(user):
    llm = OpenAI(openai_api_key=settings.OPENAI_API_KEY)
    memory = ConversationBufferMemory(memory_key="chat_history", input_key="input", output_key = "output", return_messages=True, max_token_limit=2000)

    chat_history = ChatHistory.objects.filter(user=user).order_by('-timestamp')
    formatted_history = []

    for chat in chat_history:
        formatted_history.extend([
            {"role": "user", "content": chat.message},
            {"role": "assistant", "content": chat.response}
        ])

    # Initialize memory with formatted history
    memory.save_context({"chat_history": formatted_history}, {})

    # Define the conversation logic
    conversation = RunnableWithMessageHistory(
        runnable=llm,
        memory=memory,
        input_key="input",
        output_key="output",  # Explicitly define the output key expected from the invoke method
        history_key="chat_history"
    )
    return conversation

def get_response(user_message: str, user):
    # Fetch the conversation chain configured for the user
    conversation_chain = get_conversation_chain(user)

    try:
        # Ensure the input data structure matches the expected configuration
        input_data = {"input": user_message}  # This dictionary must include the 'input' key as expected by the chain

        # Invoke the conversation chain with the correct input data
        result = conversation_chain.invoke(input_data)  # Pass the dictionary directly

        # Extract the response using the 'output' key if available, otherwise provide a default message
        response = result.get("output", "No response generated")

    except Exception as e:
        print(f"Error during conversation chain execution: {e}")
        response = "There was an error processing your request. Please try again."

    return response
