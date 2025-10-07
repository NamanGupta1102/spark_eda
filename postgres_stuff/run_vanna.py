#!/usr/bin/env python3
"""
Simple Vanna Flask App for PostgreSQL (direct connection, no env, no extras)
"""

from vanna.openai import OpenAI_Chat
from vanna.chromadb import ChromaDB_VectorStore
from vanna.flask import VannaFlaskApp


class MyVanna(ChromaDB_VectorStore, OpenAI_Chat):
    def __init__(self, config=None):
        ChromaDB_VectorStore.__init__(self, config=config)
        OpenAI_Chat.__init__(self, config=config)


def main():
    print("🚀 Starting Vanna Flask App...")

    # Initialize with OpenAI API key directly
    vn = MyVanna(config={
        'api_key': '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',
        'allow_llm_to_see_data': True
    })

    # Connect to PostgreSQL database directly
    vn.connect_to_postgres(
        host='dpg-d3g661u3jp1c73eg9v1g-a.ohio-postgres.render.com',
        dbname='crime_rate_h3u5',
        user='user1',
        password='BbWTihWnsBHglVpeKK8XfQgEPDOcokZZ',
        port=5432
    )
    print("✅ Connected to PostgreSQL database")

    # Launch the default Vanna Flask app
    app = VannaFlaskApp(vn)

    print("🌐 Open your browser and go to: http://localhost:5000")
    app.run(debug=True, host='0.0.0.0', port=5000)


if __name__ == "__main__":
    main()
