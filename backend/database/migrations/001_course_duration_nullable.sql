ALTER TABLE courses ALTER COLUMN duration_weeks DROP NOT NULL;
ALTER TABLE courses DROP CONSTRAINT IF EXISTS ck_courses_duration_positive;
ALTER TABLE courses
    ADD CONSTRAINT ck_courses_duration_positive
    CHECK (duration_weeks IS NULL OR duration_weeks > 0);
