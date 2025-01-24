import json
import os
from typing import List, Optional, Union

import requests


class GPT:

    def _call(self, prompt: List, stop: Optional[List[str]] = None, temperature: Union[int, float] = 0.2) -> str:
        header = {
            # 'Content-Type': 'text/event-stream; charset=utf-8',
            "Authorization": "Bearer " + os.environ["GPT_API_KEY"]
        }

        data = {
            "frequency_penalty": 0,
            "messages": prompt,
            "model": "gpt-4o",
            "presence_penalty": 0,
            "stream": False,
            "temperature": 0.5,
            "top_p": 1
        }

        data = requests.post(os.environ["GPT_URL"], headers=header, data=json.dumps(data))
        print(f'gpt output: {json.loads(data.content.decode("utf-8"))["choices"][0]["message"]["content"]}')
        return json.loads(data.content.decode("utf-8"))["choices"][0]["message"]["content"]



if __name__ == "__main__":
    gpt = GPT()
    ans = gpt._call([{"role": "user", "content": "你是4turbo还是4o"}])
    print(ans)