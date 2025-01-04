erDiagram
    star_metadata {
        VARCHAR2 star_id PK "Unique ID of the star (e.g., TIC ID)"
        VARCHAR2 name "Name of the star"
        NUMBER brightness "Star brightness magnitude"
        TIMESTAMP observation_time "Observation time"
        VARCHAR2 catalog "Source catalog (e.g., TESS, Kepler)"
    }

    file_paths {
        NUMBER file_id PK "Auto-incrementing file ID"
        VARCHAR2 star_id FK "Foreign key linking to star_metadata"
        VARCHAR2 file_type "Type of file (e.g., raw, processed, visualization)"
        VARCHAR2 file_name "Name of the file"
        VARCHAR2 minio_path "MinIO path to the file"
        TIMESTAMP timestamp "Timestamp of file creation/upload"
    }

    analysis_results {
        NUMBER result_id PK "Auto-incrementing result ID"
        VARCHAR2 star_id FK "Foreign key linking to star_metadata"
        NUMBER period "Orbital period detected"
        NUMBER duration "Duration of the transit"
        NUMBER depth "Depth of the transit dip"
        NUMBER power "Signal power of the detection"
        TIMESTAMP timestamp "Timestamp of result generation"
    }

    %% Relationships
    star_metadata ||--o{ file_paths : "1-to-Many"
    star_metadata ||--o{ analysis_results : "1-to-Many"
