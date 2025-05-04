import chromadb
from chromadb import PersistentClient


client = PersistentClient(
    path="./database/chroma_db" 
)

def store_frame_vectors(cam_id, frame_id, bounding_boxes, vectors, timestamp):
    
    # Initialize Chroma client and collection
    collection = client.get_or_create_collection(name="face_vectors")

    for idx, (vector, bbox) in enumerate(zip(vectors, bounding_boxes)):
        unique_id = f"{cam_id}_{frame_id}_face{idx}"

        metadata = {
            "cam_id": cam_id,
            "frame_id": frame_id,
            "x": bbox[0],
            "y": bbox[1],
            "h": bbox[2],
            "w": bbox[3],
            "timestamp": timestamp
        }

        collection.add(
            ids=[unique_id],
            embeddings=[vector],
            metadatas=[metadata],
            documents=[f"Face from {cam_id}, {frame_id}, idx: {idx}"]
        )

def store_missing(uuid, vector):
    collection = client.get_or_create_collection(name="missing_person")

    metadata = {
        "person_id": uuid
    }
    collection.add(
        ids=[uuid],                  # Unique ID for each person
        embeddings=[vector],         # Face vector (embedding)
        metadatas=[metadata],        # Optional metadata
        documents=[f"Missing person {uuid}"]  # Optional description
    )

def search_missing(vector, cam_id, top_k=5, threshold=0.75):
    collection = client.get_or_create_collection(name="face_vectors")
    # Perform similarity search
    results = collection.query(
        query_embeddings=[vector],
        n_results=top_k
    )
    # Prepare structured results
    matches = []
    for idx in range(len(results['ids'][0])):
        score = results['distances'][0][idx]
        if score <= threshold:
            metadata = results['metadatas'][0][idx]
            match = {
                "frame_id": metadata.get("frame_id"),
                "cam_id": metadata.get("cam_id", cam_id),
                "timestamp": metadata.get("timestamp"),
                "box": [metadata.get("x"),metadata.get("y"),metadata.get("h"),metadata.get("w")]
            }
            matches.append(match)
    return matches

def store_and_search_missing(uuid, vector):
    store_missing(uuid, vector)
    return search_missing(vector)