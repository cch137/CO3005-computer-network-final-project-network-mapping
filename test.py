import requests
import cbor2

text = ""

# open a text file and read it
with open(
    "./assets/journey-to-the-west/第一回-灵根育孕源流出-心性修持大道生.md", mode="r"
) as f:
    text = f.read()

# request post to localhost:6502, with JSON body { text: "hello world" }
response = requests.post("http://localhost:6502/em/", json={"text": text})

data = cbor2.loads(response.content)

for line in data:
    print(line)
