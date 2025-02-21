from google import genai
import json
from dotenv import load_dotenv
import os

load_dotenv()
api_key = os.getenv("API_KEY")

client = genai.Client(api_key=api_key)

video = input("Enter the video URL: ")

response = client.models.generate_content(
    model="gemini-2.0-flash",
    contents=f"Extract the timestamps of the most meaningful moments of this educational video: {video}. The timestamps should be of the duration of a short video. Return the timestamps in a JSON document with the following format:\n{{\n  \"meaningful_moments\": [\n    {{\"timestamp\": \"(00:00:15, 00:00:30)\", \"description\": \"Introduction to the topic\"}},\n    {{\"timestamp\": \"(00:01:30, 00:01:45)\", \"description\": \"Key concept explanation\"}},\n    {{\"timestamp\": \"(00:03:45, 00:04:25)\", \"description\": \"Example demonstration\"}},\n    {{\"timestamp\": \"(00:05:20, 00:05:55)\", \"description\": \"Summary of key points\"}}\n  ]\n}}"
)


res = response.text
res = res.strip("```json")

# Convert the JSON string to a Python dictionary
data = json.loads(res)


with open("output.json", "w") as outfile:
    json.dump(data, outfile, indent=4)




timestamps = []

with open('output.json') as f:
    data = json.load(f)
    for item in data['meaningful_moments']:
        timestamps.append(item['timestamp'])
    f.close()

ts = []

for timestamp in timestamps:
    timestamp = timestamp.strip("()")
    s = timestamp.split(",")
    tup = tuple(s)
    ts.append(tup)
    
  
print(ts)

