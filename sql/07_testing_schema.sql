CREATE TABLE IF NOT EXISTS complaint_tests (
    test_id BIGSERIAL PRIMARY KEY,

    complaint_id BIGINT NOT NULL
        REFERENCES complaints(complaint_id),

    test_number INTEGER NOT NULL
        CHECK (test_number >= 1),

    tested_by VARCHAR(150) NOT NULL
        CHECK (LENGTH(TRIM(tested_by)) >= 2),

    test_type VARCHAR(100) NOT NULL
        CHECK (LENGTH(TRIM(test_type)) >= 2),

    test_result VARCHAR(20) NOT NULL
        CHECK (test_result IN ('PASS', 'FAIL')),

    test_observations TEXT NOT NULL
        CHECK (LENGTH(TRIM(test_observations)) >= 3),

    test_notes TEXT,

    tested_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT uq_complaint_test_number
        UNIQUE (complaint_id, test_number)
);

CREATE INDEX IF NOT EXISTS idx_complaint_tests_complaint_id
    ON complaint_tests(complaint_id);

CREATE INDEX IF NOT EXISTS idx_complaint_tests_test_result
    ON complaint_tests(test_result);