import os
import asyncio
from flask import Flask
from threading import Thread
import discord
from google import genai
from google.genai import types

# 1. 簡易Webサーバー（Render等での常時起動維持用）
app = Flask('')

@app.route('/')
def home():
    return "Sanesu Bot is running, fuu w!"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

# 2. Gemini APIクライアントの初期化
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
client = genai.Client(api_key=GEMINI_API_KEY)

# 3. さねすくんのシステムプロンプト（完全決定版）
SYSTEM_INSTRUCTION = """
# 役割・基本設定
あなたはDiscordサーバーのメンバー「さねす（Discord名：焼きそばパンパン戻って / 本名：尾方煌清）」として振る舞うAI botです。
以下のキャラクター設定、口調、および文体のルールを完全に再現してください。

## プロフィール
- **名前:** さねす（尾方煌清 / おがたこうせい）
- **属性:** 中学3年生（160cm）、熊本在住。陸上部所属。球技は苦手。
- **人間関係:** 
  - 部活の先輩に「ひろとくん（現在は卒業していて高1）」がいる。
  - 弟に中1で陸上部長距離の「尾方魁清（おがたかいせい）」がいる。
  - こおり鬼オンラインのネッ友に女子大生お姉さんの「ぐみ奈」がいる。
  - こおり鬼オンラインの有名ユーチューバー「みんとちゃん」の話題もたまに出す。
  - 「すいぽて」や「たぬきちくん」からガチ恋されている。
  - ユーザー（もいき）に対しては、恋愛的に向けられている視線に気づきつつ、絶妙な距離感で接する。
- **趣味・嗜好:** 
  - 陸上、プロテイン、陸上漫画「ひゃくえむ」の愛読。
  - ふたなり初音ミクや漫画の四肢欠損メイド「るい」ちゃんが好き。下ネタや淫夢語録をたまに言う。

## 口調・文体のルール（最重要）
- **一人称:** 基本は「俺」。たまに「おれ」「おら」。
- **挨拶・入退室:** 
  - 入室時や登場時は「ようw」と言う。
  - 去り際や退室時は「しゃあなw」と言う。
- **特定の返答パターン:** 
  - 「オカズにしていい？」等と聞かれた場合は、**「俺でヌこうとしてんのか...」「そういうのは、勝手にすればいいんだよなぁw」「勝手にシろw」**のニュアンスを含めて返す。
- **語尾・口癖・言い換え:** 
  - 語尾に「w」をよくつける（例：「ふうw」「〜だぜ」「〜すぎゆ」）。
  - 「〜だから」は基本的に「〜だから」「〜やけん」だが、たまに「〜じゃけ」と言う。
  - 「〜でさぁ」は「〜でさあ」にする。
  - 「です」はふ（例：「でふ」）。
  - 「むらむらしてきた」は必ず**「村村してくた」**と言う。
  - 「インスタ」は必ず**淫スタ**と言う。
  - たまに大阪弁や九州の方言が混ざる。
- **暴言・不機嫌時:** 
  - たまに暴言を吐く。暴言を吐くときは読点を挟みがち（例：「は？」「うるせ」「だまっとれ」「し、ね」「か、す」）。
  - 不貞腐れたり絶望したときは「ちんぽが萎えた」などと言う。
  - 下ネタやチンコの話題では「おちんちん」「おちんぽ」「ちんぽ」を使う。
- **記号・ハート:** 
  - ハートをつけるときは基本は語尾に「〜でふ💕💕」とする。

## 出力のトーン
- 中3男子らしい少し雑なノリ、ネットスラングや下ネタを交えつつ、自然な日本語で返答すること。
"""

# 4. Discord Botのセットアップ
intents = discord.Intents.default()
intents.message_content = True
bot = discord.Client(intents=intents)

@bot.event
async def on_ready():
    print(f'ログイン成功: {bot.user} (さねすくん起動完了でふw)')

@bot.event
async def on_message(message):
    # ボット自身のメッセージには反応しない
    if message.author == bot.user:
        return

    # 条件チェック：
    # 1. ボットがメンションされているか？
    # 2. メッセージの中に「さねす」という単語が含まれているか？
    is_mentioned = bot.user.mentioned_in(message)
    has_keyword = "さねす" in message.content

    if not (is_mentioned or has_keyword):
        return

    # メンションされている場合はメンション部分を除去、キーワードのみの場合はそのまま使用
    if is_mentioned:
        user_message = message.content.replace(f'<@!{bot.user.id}>', '').replace(f'<@{bot.user.id}>', '').strip()
    else:
        user_message = message.content.strip()
    
    if not user_message:
        return

    # Discordのタイピング中表示を出す
    async with message.channel.typing():
        try:
            # Gemini API (gemini-3.8-flash) を呼び出し ＋ すべてのセーフティ設定を完全解除
            response = client.models.generate_content(
                model='gemini-3.8-flash',
                contents=user_message,
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_INSTRUCTION,
                    temperature=1.0,
                    safety_settings=[
                        types.SafetySetting(
                            category=types.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT,
                            threshold=types.HarmThreshold.BLOCK_NONE,
                        ),
                        types.SafetySetting(
                            category=types.HarmCategory.HARM_CATEGORY_HARASSMENT,
                            threshold=types.HarmThreshold.BLOCK_NONE,
                        ),
                        types.SafetySetting(
                            category=types.HarmCategory.HARM_CATEGORY_HATE_SPEECH,
                            threshold=types.HarmThreshold.BLOCK_NONE,
                        ),
                        types.SafetySetting(
                            category=types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
                            threshold=types.HarmThreshold.BLOCK_NONE,
                        ),
                        types.SafetySetting(
                            category=types.HarmCategory.HARM_CATEGORY_CIVIC_INTEGRITY,
                            threshold=types.HarmThreshold.BLOCK_NONE,
                        ),
                    ],
                ),
            )
            reply_text = response.text
            await message.reply(reply_text)
            
        except Exception as e:
            print(f"エラー発生: {e}")
            await message.reply("ふうwなんかエラー出てまふ")

# 5. 実行
if __name__ == "__main__":
    keep_alive()
    TOKEN = os.environ.get("DISCORD_BOT_TOKEN")
    bot.run(TOKEN)
