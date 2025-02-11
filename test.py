from google import genai
import json
from dotenv import load_dotenv
import os

load_dotenv()
api_key = os.getenv("API_KEY")

client = genai.Client(api_key=api_key)

#video = input("Enter the video URL: ")
'''
response = client.models.generate_content(
    model="gemini-2.0-flash",
    contents=f"Extract the timestamps of the most meaningful moments of this educational video: {video}. The timestamps should be of the duration of a short video. Return the timestamps in a JSON document with the following format:\n{{\n  \"meaningful_moments\": [\n    {{\"timestamp\": \"(00:15, 00:30)\", \"description\": \"Introduction to the topic\"}},\n    {{\"timestamp\": \"(01:30, 01:45)\", \"description\": \"Key concept explanation\"}},\n    {{\"timestamp\": \"(03:45, 04:25)\", \"description\": \"Example demonstration\"}},\n    {{\"timestamp\": \"(05:20, 05:55)\", \"description\": \"Summary of key points\"}}\n  ]\n}}"
)
'''

response = '''
{
  "meaningful_moments": [
    {"timestamp": "(00:00, 00:41)", "description": "Introduction to backpropagation and neural networks"},
    {"timestamp": "(01:46, 02:40)", "description": "Visualizing the gradient descent process"},
    {"timestamp": "(04:08, 05:05)", "description": "Explanation of how error propagates back through the network"},
    {"timestamp": "(06:50, 07:55)", "description": "Analogy of backpropagation with moving bricks"},
    {"timestamp": "(09:05, 10:00)", "description": "Mathematical formulation of backpropagation (partial derivatives)"},
    {"timestamp": "(11:54, 12:40)", "description": "Detailed example calculation of backpropagation for one layer"},
    {"timestamp": "(14:00, 14:44)", "description": "Addressing common misconceptions and importance of learning rate"}
  ]
}
'''

# Convert the JSON string to a Python dictionary
data = json.loads(response)


with open("output.json", "w") as outfile:
    json.dump(data, outfile, indent=4)




timestamps = {}

with open('meaningful_moments.json') as f:
    data = json.load(f)
    for item in data['meaningful_moments']:
        timestamps[item['description']] = item['timestamp']
    f.close()

  


print(timestamps)