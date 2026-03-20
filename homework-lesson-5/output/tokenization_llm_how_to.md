# Tokenization в LLM: як робити

## Огляд
Цей документ пояснює, що таке токенізація для великих мовних моделей (LLM), які алгоритми використовуються, коли і як навчити власний токенайзер, а також практичні рекомендації й приклади коду (Python).

## Ключова інформація

- Мета токенізації: перетворити текст (символи) у послідовність токенів (цілі числа), які подає модель. Також включає додавання спецтокенів (BOS, EOS, PAD, UNK, MASK).
- Популярні підходи:
  - BPE (Byte Pair Encoding) — ітеративне злиття найчастіше суміжних пар символів/ніграм; часто використовується в GPT-подібних моделях.
  - Byte-level BPE — BPE над байтами (256 базових токенів) — працює з будь-якими Unicode-символами без <unk> (напр., GPT-2).
  - WordPiece — схоже на BPE, використовувався для BERT (deterministic merge rules).
  - Unigram (SentencePiece Unigram) — починає з великого набору кандидатів і послідовно видаляє найменш важливі; може бути стохастичним при розбитті.
  - SentencePiece — бібліотека, яка робить BPE або Unigram поверх сирого тексту (корисно для мов без пробілів).

- Вибір алгоритму залежить від задачі і мови. Для багатомовних/немов із пробілами краще SentencePiece; для узгодженості з GPT-style моделями — byte-level BPE.
- Вплив словника: розмір словника (vocab size) впливає на компроміс: великі словники — менше субслов, але більше параметрів токенайзера; маленькі — більше розбиття слів.
- Нормалізація тексту та препроцесинг (Unicode normalization, lowercasing, NFKC, видалення контролів) важливі перед навчанням.

## Як навчити свій токенайзер — кроки (й коротко: приклад BPE через Hugging Face Tokenizers)

1. Підготуйте корпус
   - Великий, репрезентативний для вашої задачі (мова / домен). Очищення: прибрати дуже короткі дублі, некоректні бінарні блоки, метадані, якщо потрібно.
2. Визначте параметри
   - Алгоритм: BPE / byte-level BPE / Unigram / WordPiece
   - Розмір словника: 20k, 32k, 50k тощо (залежить від мови і моделі)
   - Спецтокени: [PAD], [UNK], [CLS]/<s>, [SEP]/</s>, [MASK], [BOS], [EOS]
   - Нормалізація: NFC/NFKC, lowercasing?
3. Тренуйте токенайзер
   - Використайте: Hugging Face tokenizers або SentencePiece. Наведено приклад нижче.
4. Перевірте/дебажте
   - Переведіть приклади тексту в токени й назад (decode). Перевірте частоту subword-розбиття для різних мов.
   - Оцініть число токенів на слово і довжину послідовностей.
5. Збережіть і використовуйте в пайплайні тренування LLM (включно з padding/truncation, attention masks).

## Практичний приклад: тренування byte-level BPE з Python (tokenizers)

Приклад з бібліотеки tokenizers (Hugging Face). Це скорочений шаблон:

from tokenizers import Tokenizer, models, trainers, pre_tokenizers, processors

# 1) Ініціалізуємо модель BPE з byte-level (як у GPT-2)
tokenizer = Tokenizer(models.BPE())
# 2) Нормалізація і препроцесинг (опційно)
from tokenizers import normalizers
from tokenizers.normalizers import NFKC
tokenizer.normalizer = NFKC()
# 3) Pre-tokenizer: byte-level
from tokenizers.pre_tokenizers import ByteLevel
tokenizer.pre_tokenizer = ByteLevel()

# 4) Тренер для BPE (вказуємо розмір вокабуляру і спецтокени)
trainer = trainers.BpeTrainer(vocab_size=50257, special_tokens=["<|pad|>", "", "<|unk|>"])

# 5) Навчання на файлах-корпусах (list_of_files)
files = ["data/corpus1.txt", "data/corpus2.txt"]
tokenizer.train(files, trainer)

# 6) Після тренування: додати постпроцесор (наприклад, EOS/BOS)
from tokenizers.processors import TemplateProcessing
tokenizer.post_processor = TemplateProcessing(single="$A </s>", special_tokens=[("</s>", tokenizer.token_to_id("</s>"))])

# Зберегти
tokenizer.save("my_byte_bpe.json")

Примітка: для більш простого інтерфейсу з Transformers можна створити Hugging Face Tokenizer через AutoTokenizer після конвертації / пакування словника.

## Приклад: використати готовий токенайзер (Transformers)
from transformers import AutoTokenizer

auto_tokenizer = AutoTokenizer.from_pretrained('gpt2')
text = "Привіт, як справи?"
encoded = auto_tokenizer(text, return_tensors='pt')
print(encoded)

## Поради й тонкощі
- Для мов з багатьма діакритиками/специфічними символами зазвичай краще byte-level або sentencepiece.
- Якщо плануєте fine-tune на існуючій моделі — використайте її токенайзер (щоб відповідали індекси ембеддінгів).
- Оцініть компроміс: токени/слово, speed, vocab size.
- Контролюйте спецтокени: інколи треба додати домен-специфічні токени (наприклад, <URL>, <EMAIL>, технічні терміни).
- Padding/Truncation й attention mask повинні бути узгоджені з архітектурою моделі — padding справа/зліва залежно від моделі.

## Порівняння (коротко)
- BPE / byte-level BPE: просте, детерміноване, добре для англійської та багатьох латинських мов; byte-level покриває Unicode.
- WordPiece: схоже на BPE, використовувався в BERT (довірений для англомовних моделей).
- Unigram / SentencePiece: краще для мов без пробілів або для багатомовних моделей; може давати різні токенізації (sampling).

## Ключові висновки
- Токенізація — фундаментальний крок: впливає на ефективність моделі, використання пам'яті та якість для різних мов.
- Вибір алгоритму залежить від мови, доступного корпусу і сумісності з моделлю (власна модель vs донавчання існуючої).
- Для production: перевіряйте декодування, додайте необхідні спецтокени, збережіть і документуйте версію токенайзера.

## Джерела
- "Large language model" (excerpt) — локальна база знань: опис BPE, WordPiece, Unigram, спецтокенів [local]
- Hugging Face 12 Tokenization algorithms (Transformers docs) — детальний опис BPE, byte-level BPE, Unigram, SentencePiece, WordPiece [web]

