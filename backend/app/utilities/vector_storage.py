from chromadb import PersistentClient
from app.utilities.logger_config import logger

# Initialize the Chroma client and collections once at module load
db_path = "./databases/chroma_db"
client = PersistentClient(path=db_path)

# Collections for storing frame face vectors and missing-person embeddings
face_collection = client.get_or_create_collection(
    name="face_vectors",
    metadata={"hnsw:space": "cosine"}
)
missing_collection = client.get_or_create_collection(
    name="missing_person",
    metadata={"hnsw:space": "cosine"}
)

def store_frame_vectors(cam_id: str,
                        frame_id: str,
                        bounding_boxes: list[tuple[float, float, float, float]],
                        vectors: list[list[float]],
                        timestamp: float) -> None:
    """
    Store face embeddings for a single video frame.

    Args:
        cam_id:       Identifier for the camera.
        frame_id:     Identifier for the video frame.
        bounding_boxes: List of (x, y, w, h) tuples for each face.
        vectors:      List of corresponding embedding vectors.
        timestamp:    Unix timestamp for when the frame was captured.
    """
    if len(bounding_boxes) != len(vectors):
        logger.error("Number of bounding boxes must match number of vectors.")
        raise ValueError("Number of bounding boxes must match number of vectors.")

    for idx, (vector, bbox) in enumerate(zip(vectors, bounding_boxes)):
        x, y, w, h = bbox
        unique_id = f"{cam_id}_{frame_id}_face{idx}"

        metadata = {
            "cam_id": cam_id,
            "frame_id": frame_id,
            "x": x,
            "y": y,
            "w": w,
            "h": h,
            "timestamp": timestamp
        }

        face_collection.add(
            ids=[unique_id],
            embeddings=[vector],
            metadatas=[metadata],
            documents=[f"Face {idx} from {cam_id} frame {frame_id}"]
        )


def store_missing(person_id: str, vector: list[float]) -> None:
    """
    Store the embedding for a missing person.

    Args:
        person_id: Unique identifier for the person.
        vector:    Embedding vector for the person's face.
    """
    metadata = {"person_id": person_id}

    # Use upsert to overwrite any existing embedding for the same ID
    missing_collection.upsert(
        ids=[person_id],
        embeddings=[vector],
        metadatas=[metadata],
        documents=[f"Missing person {person_id}"]
    )


def search_matches(query_vector: list[float],
                   top_k: int = 2000,
                   max_distance: float = 0.5) -> list[dict]:
    """
    Search stored frame vectors for close matches to the query vector.

    Args:
        query_vector:   Embedding to search for.
        top_k:          Number of nearest neighbors to return.
        max_distance:   Maximum allowable distance (cosine distance) for a match.

    Returns:
        List of dicts with match info: frame_id, cam_id, score, box, timestamp.
    """
    results = face_collection.query(
        query_embeddings=[query_vector],
        n_results=top_k
    )

    matches = []
    distances = results.get("distances", [[]])[0]
    metadatas = results.get("metadatas", [[]])[0]

    for dist, md in zip(distances, metadatas):
        # Lower distance means more similar under cosine metric
        if dist <= max_distance:
            matches.append({
                "cam_id": md["cam_id"],
                "frame_id": md["frame_id"],
                "timestamp": md["timestamp"],
                "score": dist,
                "box": [md["x"], md["y"], md["w"], md["h"]]
            })
    return sorted(matches,key=lambda x: x["timestamp"])


def store_and_search_missing(person_id: str,
                              query_vector: list[float],
                              top_k: int = 2000,
                              max_distance: float = 0.5) -> list[dict]:
    """
    Store a missing-person embedding and then search for matches in stored frame vectors.
    """
    store_missing(person_id, query_vector)
    return search_matches(query_vector, top_k=top_k, max_distance=max_distance)

def get_vector(uuid: str) -> list[dict]:
    results = missing_collection.get(
        where={"person_id": uuid},
        include=["embeddings", "metadatas"],
    )
    logger.info(f"Retrieved vector for UUID {uuid}: {results}")
    return results.get("embeddings", [[]])[0]