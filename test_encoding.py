import fitz  # PyMuPDF, for PDF processing
import spacy  
import os 
import numpy as np  

# Load English NLP model with word vectors
#   (e.g., en_core_web_md or en_core_web_lg)
nlp = spacy.load("en_core_web_md") 

def load_keywords_and_vectors(folder="."):
    categories = {}
    category_vectors = {}
    for filename in os.listdir(folder):
        if filename.endswith(".txt"):
            category = filename.replace(".txt", "")
            with open(os.path.join(folder, filename), "r") as file:
                keywords = [line.strip().lower() for line in file]
                categories[category] = keywords

                # Compute an average vector for the category keywords
                category_vectors[category] = np.mean([nlp(keyword).vector for keyword in keywords if nlp(keyword).has_vector], axis=0)
    return categories, category_vectors

keywords, category_vectors = load_keywords_and_vectors()

category_colors = {
    "Opportunity": (0, 255, 0),  # Green
    "Risk": (255, 0, 0),         # Red
    "Replace": (255, 192, 203),  # Pink
    "Complement": (255, 255, 0), # Yellow
}

def classify_with_embeddings(sentence):
    sentence_vector = nlp(sentence).vector
    if not sentence_vector.any():  # Skip sentences without valid vectors
        return None
    similarities = {
        category: np.dot(sentence_vector, category_vector) / (np.linalg.norm(sentence_vector) * np.linalg.norm(category_vector))
        for category, category_vector in category_vectors.items()
    }

    # Find the category with the highest similarity
    best_category = max(similarities, key=similarities.get)
    return best_category if similarities[best_category] > 0.5 else None  # Threshold here

# Input and output folders
input_folder = "pdf"
output_folder = "output"
os.makedirs(output_folder, exist_ok=True)

# Process each PDF in the input folder
for filename in os.listdir(input_folder):
    if filename.endswith(".pdf"): 
        pdf_path = os.path.join(input_folder, filename)
        output_path = os.path.join(output_folder, filename)
        
        doc = fitz.open(pdf_path)

        for page in doc:
            text = page.get_text("text")
            doc_nlp = nlp(text)
            
            for sentence in doc_nlp.sents:
                category = classify_with_embeddings(sentence.text)
                if category:
                    # Find bounding boxes for each word in the sentence
                    words = page.search_for(sentence.text)
                    for word_rect in words:
                        color = category_colors.get(category, (0, 0, 0))  # Default to black if no match
                        normalized_color = tuple(c / 255 for c in color)  # ... and colors require normalization
                        page.draw_rect(word_rect, color=normalized_color, fill_opacity=0.2)

        doc.save(output_path)
        print(f"* Processed and saved: {output_path}")

print("- All PDFs have been processed ---")
