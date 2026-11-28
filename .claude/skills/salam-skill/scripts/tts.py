#!/usr/bin/env python3
"""تعليق صوتي مجاني (edge-tts) مع توقيت كل كلمة.

  tts.py voice.txt -o voice.mp3 --words words.json [--voice ar-IQ-BasselNeural] [--rate +8%]

أصوات مفيدة: ar-IQ-BasselNeural / ar-IQ-RanaNeural (عراقي)، ar-SA-HamedNeural (سعودي)، ar-EG-ShakirNeural (مصري).
في الحاوية السحابية الوكيل يستخدم شهادة خاصة، فنوجّه certifi إليها تلقائياً.
"""
import argparse, asyncio, json, os


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('text'); ap.add_argument('-o', default='voice.mp3'); ap.add_argument('--words', default='words.json')
    ap.add_argument('--voice', default='ar-IQ-BasselNeural'); ap.add_argument('--rate', default='+8%'); ap.add_argument('--pitch', default='+0Hz')
    a = ap.parse_args()
    ca = '/root/.ccr/ca-bundle.crt'
    if os.path.exists(ca):
        import certifi; certifi.where = lambda: ca
    import edge_tts
    text = open(a.text, encoding='utf-8').read().strip()

    async def run():
        com = edge_tts.Communicate(text, a.voice, rate=a.rate, pitch=a.pitch, boundary='WordBoundary')
        words = []
        with open(a.o, 'wb') as f:
            async for ch in com.stream():
                if ch['type'] == 'audio':
                    f.write(ch['data'])
                elif ch['type'] == 'WordBoundary':
                    s = ch['offset'] / 1e7
                    words.append({'w': ch['text'], 'start': round(s, 3), 'end': round(s + ch['duration'] / 1e7, 3)})
        return words
    words = asyncio.run(run())
    json.dump(words, open(a.words, 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
    print(f'  {a.o}  ({len(words)} words, last at {words[-1]["end"] if words else 0}s)')


if __name__ == '__main__':
    main()
