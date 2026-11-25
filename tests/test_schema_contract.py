import unittest
from pathlib import Path

from verify_database_schema import EXPECTED_TABLES, verify_schema


class SchemaContractTests(unittest.TestCase):
    def test_sql_files_exist_and_define_expected_tables(self):
        sql_dir = Path("app/database")
        combined_sql = "\n".join(
            (sql_dir / name).read_text(encoding="utf-8")
            for name in ("schema.sql", "operations_schema.sql", "settlement_schema.sql")
        )
        for table in EXPECTED_TABLES:
            self.assertIn(f"CREATE TABLE IF NOT EXISTS {table}", combined_sql)

    def test_in_memory_schema_verification(self):
        verify_schema(":memory:")


if __name__ == "__main__":
    unittest.main()
