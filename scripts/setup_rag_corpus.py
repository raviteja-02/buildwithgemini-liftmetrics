import sys
import vertexai
from vertexai.preview import rag
from vertexai.preview.rag.utils import resources as rr

PROJECT_ID = "qwiklabs-gcp-03-fde3effbf431"
LOCATION = "us-central1"
GCS_PATH = "gs://liftmetrics-media-fde3effbf431/rag_docs/training_science_guide.txt"

PARSING_PROMPT = (
    "Extract the key evidence-based strength and hypertrophy principles, volume landmarks (MV, MEV, MAV, MRV), "
    "inter-set rest intervals, RPE/RIR guidelines, deload protocols, and protein recommendations. "
    "Output clear, authoritative, self-contained guidance."
)

print(f"Initializing Vertex AI in {LOCATION} for project {PROJECT_ID}...")
vertexai.init(project=PROJECT_ID, location=LOCATION)

# 1. Switch region to serverless mode
cfg = f"projects/{PROJECT_ID}/locations/{LOCATION}/ragEngineConfig"
try:
    rag.update_rag_engine_config(
        rag_engine_config=rag.RagEngineConfig(
            name=cfg,
            rag_managed_db_config=rag.RagManagedDbConfig(mode=rr.Serverless()),
        )
    )
    print("✓ RAG engine config set to Serverless mode.")
except Exception as e:
    print(f"Notice during update_rag_engine_config: {e}")

# 2. Create the corpus
print("Creating RAG corpus 'liftmetrics-sports-science'...")
corpus = rag.create_corpus(
    display_name="liftmetrics-sports-science",
    embedding_model_config=rag.EmbeddingModelConfig(
        publisher_model="publishers/google/models/text-embedding-005"
    ),
)
print("✓ Corpus created successfully:", corpus.name)

# 3. Import + parse + chunk + embed
print(f"Importing and indexing {GCS_PATH}...")
resp = rag.import_files(
    corpus_name=corpus.name,
    paths=[GCS_PATH],
    transformation_config=rag.TransformationConfig(
        chunking_config=rag.ChunkingConfig(chunk_size=512, chunk_overlap=100)
    ),
    llm_parser=rag.LlmParserConfig(
        model_name="gemini-3.6-flash",
        custom_parsing_prompt=PARSING_PROMPT,
    ),
)
print(f"✓ Indexing complete! Imported count: {resp.imported_rag_files_count}")

# 4. Save corpus name to a local file for the agent to read
with open("/config/Desktop/BuildWithGemini/liftmetrics/scripts/corpus_resource.txt", "w") as f:
    f.write(corpus.name.strip())
print("✓ Saved corpus resource name to scripts/corpus_resource.txt")
