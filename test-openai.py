from openai import OpenAI
import os

# Set your OpenAI API key
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


messages = [{"role": "system", "content": "You are a intelligent assistant."}]
while True:
    message = input("User : ")
    if message:
        messages.append(
            {"role": "user", "content": message},
        )
        # chat = openai.ChatCompletion.create(model="gpt-3.5-turbo", messages=messages)
        response = client.chat.completions.create(
            model="gpt-3.5-turbo", messages=[{"role": "user", "content": message}]
        )

    reply = response.choices[0].message.content
    print(f"ChatGPT: {reply}")
    messages.append({"role": "assistant", "content": reply})
