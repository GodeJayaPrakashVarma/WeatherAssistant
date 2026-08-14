import os
from dotenv import load_dotenv
from groq import Groq
import json
import requests
import gradio as gr

load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

client = Groq(api_key = GROQ_API_KEY)

def get_weather(location):
    WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")
    url = f"http://api.openweathermap.org/data/2.5/weather?q={location}&units=metric&appid={WEATHER_API_KEY}"
    resposne = requests.get(url)
    data = resposne.json()

    if data.get("cod") == 200:
        return {
            "location" : location,
            "temperature" : data["main"]["temp"],
            "description" : data["weather"][0]["description"]
        }
    else:
        return {"error" : "City not found"}


def ask(location: str) -> str:
    tools = [{
        "type" : "function",
        "function" : {
            "name" : "get_weather",
            "description" : "Get current weather for a city",
            "parameters" : {
                "type" : "object",
                "properties" : {
                    "location" :{
                        "type" : "string",
                        "description" : "City name like Hyderabad, London"
                    }
                },
                "required" : ["location"]
            }
        }
    }]

    messages = [
        {
            "role" : "system",
            "content" : "You are  a weather assistant. Use get_weather function when asked about weather."
        },
        {
            "role" : "user",
            "content" : f"What's the weather in {location}?"
        }
    ]

    response = client.chat.completions.create(
    model="llama-3.3-70b-versatile",
    messages=messages,
    tools=tools,
    tool_choice="auto"
    )

    response_message = response.choices[0].message

    if response_message.tool_calls:
        tool_call = response_message.tool_calls[0]
        arguments = json.loads(tool_call.function.arguments)
        location = arguments["location"]
        weather_data = get_weather(location)
        messages.append(response_message)
        messages.append({
            "role" : "tool",
            "tool_call_id" : tool_call.id,
            "name" : tool_call.function.name,
            "content" : json.dumps(weather_data)
        })

    final_response = client.chat.completions.create(
        messages = messages,
        model = "llama-3.3-70b-versatile",
        tools = tools,
        tool_choice = "auto"
    )
    return final_response.choices[0].message.content

print(ask("Parnasala"))
demo = gr.Interface(
    fn=ask,
    inputs=[gr.Textbox(lines=1, placeholder="Enter location name", label="Location")],
    outputs=[gr.Textbox(lines=4, label="Weather")],
    title="Weather Assistant",
    description="Enter the name of the location to get the weather"
)

demo.launch(share=True)
