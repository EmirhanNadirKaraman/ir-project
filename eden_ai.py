import json
import requests

API_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoiOGY2MTE2MjEtNTJiMi00NTE2LWJiOGYtZGQzYjYzNTU5NzNhIiwidHlwZSI6ImFwaV90b2tlbiJ9.koJFVMgNEgs6gPtZUGtKKmVm10AePdisbMLH0mo5sW8"


def get_labels(image_url: str, provider="google") -> list:
    headers = {"Authorization": f"Bearer {API_KEY}"}

    url = "https://api.edenai.run/v2/image/object_detection"
    json_payload = {
        "providers": f"{provider}",
        "file_url": f"{image_url}",
    }

    response = requests.post(url, json=json_payload, headers=headers)

    result = json.loads(response.text)
    return [
        {
            "label": prediction["label"],
            "confidence": prediction["confidence"],
        }
        for prediction in result[provider]["items"]
    ]


def get_topics(text: str) -> list[str]:
    return ["enis"]


def print_json(s):
    print(json.dumps(s, indent=3))


def main():
    image_url = "https://fiverr-res.cloudinary.com/images/q_auto,f_auto/gigs/192266122/original/532ba16adbed3307c900855065fa7a5bdbeb1596/design-mrbeast-style-thumbnail.jpg"
    labels = get_labels(image_url, provider="amazon")
    print_json(labels)


if __name__ == "__main__":
    main()
