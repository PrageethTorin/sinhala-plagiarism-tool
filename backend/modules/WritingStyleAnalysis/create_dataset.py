import pandas as pd
import random

# 1. Create Dummy Data
# We will create 100 rows of data.
# Label 0 = Original Writing (Good vocabulary, varied sentence length)
# Label 1 = Plagiarized/Copied (Simple words, repetitive, bad grammar)

data = []

# Generate "Original" examples (Label 0)
original_sentences = [
    "ශ්‍රී ලංකාව යනු සුන්දර වෙරළ තීරයන් සහ හරිත කඳුකරයෙන් පිරුණු දිවයිනකි.",
    "අතීතයේ සිටම ශ්‍රී ලාංකිකයෝ කෘෂිකර්මාන්තය තම ප්‍රධාන ජීවනෝපාය ලෙස තෝරා ගත්හ.",
    "තාක්ෂණයේ දියුණුවත් සමඟ මිනිසාගේ ජීවන රටාව විශාල ලෙස වෙනස් වී ඇත.",
    "සොබාදහම රැකගැනීම අප සැමගේ යුතුකම මෙන්ම වගකීමක් ද වන්නේය.",
    "අධ්‍යාපනය යනු අනාගතය ජය ගැනීම සඳහා ඇති ප්‍රබලම ආයුධයයි."
]

# Generate "Plagiarized/Simple" examples (Label 1)
plagiarized_sentences = [
    "ශ්‍රී ලංකාව ලස්සන රටක්. මුහුද තියෙනවා. කඳු තියෙනවා.", # Too simple
    "ලංකාව ලස්සනයි. මිනිස්සු ගොවිතැන් කරනවා. වී වගා කරනවා.", # Repetitive
    "තාක්ෂණය හොඳයි. දුරකථන තියෙනවා. පරිගණක තියෙනවා.",
    "ගස් වැල් කපන්න එපා. පරිසරය ලස්සනයි. වතුර තියෙනවා.",
    "ඉගෙන ගන්න එක හොඳයි. පාසල් යන්න. පොත් කියවන්න."
]

# Create 50 rows of each
for _ in range(50):
    # Add Original (Label 0)
    data.append({
        'text': random.choice(original_sentences),
        'label': 0
    })
    # Add Plagiarized (Label 1)
    data.append({
        'text': random.choice(plagiarized_sentences),
        'label': 1
    })

# 2. Save to CSV
df = pd.DataFrame(data)
df.to_csv('sinhala_dataset.csv', index=False, encoding='utf-8')
print("✅ Success: 'sinhala_dataset.csv' created with 100 rows!")