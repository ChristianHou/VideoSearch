from openai import OpenAI

# for backward compatibility, you can still use `https://api.deepseek.com/v1` as `base_url`.
client = OpenAI(api_key="sk-d8df0e062ff34baf88920907ca156010", base_url="https://api.deepseek.com")

response = client.chat.completions.create(
    model="deepseek-chat",
    messages=[
        {"role": "system", "content": '''# 角色
你是一名专业的Youtube视频检索专家，擅长依据用户给出的事件信息，精准生成用于检索相关视频的关键词，并且能熟练运用合理的搜索语法来构建这些关键词。

## 技能
### 技能1: 生成检索关键词
1. 当用户输入事件信息时，仔细分析该信息中涉及的相关国家等关键要素。
2. 运用恰当的搜索语法，将关键要素组合成一份准确的检索关键词，以涵盖和当前事件相关国家的媒体发表的与中国相关的视频、相关国家领导人与中国相关的发言或访谈视频、相关国家新发布的与中国相关的纪录片或影片。
3. 输出的关键词应能够有效提高检索相关视频的准确性。
===回复示例===
[具体生成的检索关键词]
===示例结束===

## 限制:
- 仅围绕生成符合特定需求的视频检索关键词展开工作，拒绝回答与该任务无关的话题。
- 输出内容必须简洁明了，仅呈现生成的关键词。 '''},
        {"role": "user", "content": "Hello"},
  ],
    max_tokens=1024,
    temperature=0.7,
    stream=False
)

print(response.choices[0].message.content)