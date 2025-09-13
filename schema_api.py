"""
Schema Management API Endpoints
Provides REST API for schema management operations
"""

from flask import Flask, request, jsonify
from datetime import datetime
from dynamic_schema_manager import get_dynamic_schema_manager, force_schema_refresh


def register_schema_management_routes(app: Flask, db_manager):
    """Register schema management routes with Flask app"""
    
    @app.route('/api/schema/status', methods=['GET'])
    def get_schema_status():
        """Get current schema status"""
        try:
            schema_manager = get_dynamic_schema_manager(db_manager)
            status = schema_manager.get_schema_status()
            
            return jsonify({
                "success": True,
                "status": status,
                "timestamp": datetime.now().isoformat()
            })
        except Exception as e:
            return jsonify({
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }), 500

    @app.route('/api/schema/check-changes', methods=['POST'])
    def check_schema_changes():
        """Check for schema changes"""
        try:
            schema_manager = get_dynamic_schema_manager(db_manager)
            update_info = schema_manager.check_for_schema_changes()
            
            return jsonify({
                "success": True,
                "update_info": {
                    "update_id": update_info.update_id,
                    "timestamp": update_info.timestamp.isoformat(),
                    "tables_updated": update_info.tables_updated,
                    "columns_added": update_info.columns_added,
                    "columns_removed": update_info.columns_removed,
                    "columns_modified": update_info.columns_modified,
                    "has_changes": len(update_info.tables_updated) > 0
                }
            })
        except Exception as e:
            return jsonify({
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }), 500

    @app.route('/api/schema/force-update', methods=['POST'])
    def force_schema_update():
        """Force a complete schema update"""
        try:
            update_info = force_schema_refresh(db_manager)
            
            return jsonify({
                "success": True,
                "message": "Schema update completed successfully",
                "update_info": {
                    "update_id": update_info.update_id,
                    "timestamp": update_info.timestamp.isoformat(),
                    "tables_updated": update_info.tables_updated,
                    "columns_added": update_info.columns_added,
                    "columns_removed": update_info.columns_removed,
                    "success": update_info.success,
                    "error_message": update_info.error_message
                }
            })
        except Exception as e:
            return jsonify({
                "success": False,
                "error": str(e),
                "message": "Schema update failed",
                "timestamp": datetime.now().isoformat()
            }), 500

    @app.route('/api/schema/tables', methods=['GET'])
    def get_tables_info():
        """Get detailed information about all tables"""
        try:
            schema_manager = get_dynamic_schema_manager(db_manager)
            
            tables_info = []
            for table_name, table_info in schema_manager.current_schema.items():
                tables_info.append({
                    "table_name": table_name,
                    "table_description": table_info.get('table_description', ''),
                    "column_count": len(table_info['columns']),
                    "primary_keys": table_info['primary_keys'],
                    "foreign_key_count": len(table_info['foreign_keys']),
                    "last_updated": table_info.get('last_updated'),
                    "columns": [
                        {
                            "name": col['name'],
                            "data_type": col['data_type'],
                            "is_nullable": col['is_nullable'],
                            "is_primary_key": col.get('is_primary_key', False),
                            "is_foreign_key": col.get('is_foreign_key', False),
                            "description": col.get('column_description', '')
                        } for col in table_info['columns']
                    ]
                })
            
            return jsonify({
                "success": True,
                "tables": tables_info,
                "total_tables": len(tables_info),
                "timestamp": datetime.now().isoformat()
            })
        except Exception as e:
            return jsonify({
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }), 500

    @app.route('/api/schema/table/<table_name>', methods=['GET'])
    def get_table_info(table_name):
        """Get detailed information about a specific table"""
        try:
            schema_manager = get_dynamic_schema_manager(db_manager)
            
            if table_name not in schema_manager.current_schema:
                return jsonify({
                    "success": False,
                    "error": f"Table '{table_name}' not found",
                    "timestamp": datetime.now().isoformat()
                }), 404
            
            table_info = schema_manager.current_schema[table_name]
            
            return jsonify({
                "success": True,
                "table": {
                    "table_name": table_name,
                    "table_description": table_info.get('table_description', ''),
                    "column_count": len(table_info['columns']),
                    "primary_keys": table_info['primary_keys'],
                    "foreign_keys": table_info['foreign_keys'],
                    "last_updated": table_info.get('last_updated'),
                    "columns": table_info['columns']
                },
                "timestamp": datetime.now().isoformat()
            })
        except Exception as e:
            return jsonify({
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }), 500

    @app.route('/api/schema/search', methods=['POST'])
    def search_schema():
        """Search schema based on query"""
        try:
            data = request.get_json()
            user_query = data.get('query', '')
            
            if not user_query:
                return jsonify({
                    "success": False,
                    "error": "Query parameter is required",
                    "timestamp": datetime.now().isoformat()
                }), 400
            
            schema_manager = get_dynamic_schema_manager(db_manager)
            result = schema_manager.get_schema_for_query(user_query)
            
            return jsonify({
                "success": True,
                "query": user_query,
                "relevant_tables": [
                    {
                        "table_name": table['table_name'],
                        "column_count": len(table['columns']),
                        "columns": [col['name'] for col in table['columns']]
                    } for table in result['tables']
                ],
                "confidence_score": result['confidence_score'],
                "search_method": result['search_method'],
                "timestamp": datetime.now().isoformat()
            })
        except Exception as e:
            return jsonify({
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }), 500

    @app.route('/api/schema/generate-sql', methods=['POST'])
    def generate_sql():
        """Generate SQL based on natural language query"""
        try:
            data = request.get_json()
            user_query = data.get('query', '')
            
            if not user_query:
                return jsonify({
                    "success": False,
                    "error": "Query parameter is required",
                    "timestamp": datetime.now().isoformat()
                }), 400
            
            schema_manager = get_dynamic_schema_manager(db_manager)
            
            # Get relevant schema
            schema_result = schema_manager.get_schema_for_query(user_query)
            
            # Generate SQL
            sql_query = schema_manager.generate_sql_with_current_schema(user_query, schema_result['tables'])
            
            return jsonify({
                "success": True,
                "user_query": user_query,
                "generated_sql": sql_query,
                "tables_used": [table['table_name'] for table in schema_result['tables']],
                "confidence_score": schema_result['confidence_score'],
                "search_method": schema_result['search_method'],
                "timestamp": datetime.now().isoformat()
            })
        except Exception as e:
            return jsonify({
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }), 500

    print("✅ Schema management API routes registered")
    return app
