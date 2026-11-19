"""
JAK Data Analytics - API Schema Service

Features:
- Register reusable API schemas
- Validate schema definitions
- Validate incoming request data
- Required and optional fields
- Data type validation
- Nested object validation
- Array validation
- Minimum and maximum constraints
- String length validation
- Enum validation
- Schema listing and removal
- Schema export
"""

from __future__ import annotations

import copy
import json
import re

from datetime import date, datetime
from typing import Any, Dict, List, Optional


class APISchemaError(Exception):
    """Base exception for API schema operations."""


class SchemaNotFoundError(APISchemaError):
    """Raised when a requested schema does not exist."""


class SchemaValidationError(APISchemaError):
    """Raised when a schema definition is invalid."""


class APIDataValidationError(APISchemaError):
    """Raised when data does not match a schema."""


SUPPORTED_TYPES = {
    "string",
    "integer",
    "number",
    "boolean",
    "object",
    "array",
    "date",
    "datetime",
    "email",
    "uuid",
    "any",
}


SCHEMA_OPTIONS = {
    "required",
    "nullable",
    "min",
    "max",
    "min_length",
    "max_length",
    "pattern",
    "enum",
    "items",
    "properties",
    "additional_properties",
    "description",
}


class APISchemaService:

    def __init__(self):
        self.schemas: Dict[str, Dict[str, Any]] = {}

    # -----------------------------------------------------
    # SCHEMA VALIDATION
    # -----------------------------------------------------

    def validate_schema_definition(
        self,
        schema: Dict[str, Any],
        path: str = "schema",
    ) -> Dict[str, Any]:

        errors = []

        if not isinstance(schema, dict):
            return {
                "valid": False,
                "errors": [f"{path} must be a dictionary."],
            }

        schema_type = schema.get("type")

        if schema_type not in SUPPORTED_TYPES:
            errors.append(
                f"{path}.type must be one of: "
                + ", ".join(sorted(SUPPORTED_TYPES))
            )
            return {"valid": False, "errors": errors}

        unknown_options = set(schema.keys()) - SCHEMA_OPTIONS

        if unknown_options:
            errors.append(
                f"{path} contains unsupported options: "
                + ", ".join(sorted(unknown_options))
            )

        if "required" in schema and not isinstance(
            schema["required"], bool
        ):
            errors.append(f"{path}.required must be a boolean.")

        if "nullable" in schema and not isinstance(
            schema["nullable"], bool
        ):
            errors.append(f"{path}.nullable must be a boolean.")

        if schema_type == "object":

            properties = schema.get("properties", {})

            if not isinstance(properties, dict):
                errors.append(
                    f"{path}.properties must be a dictionary."
                )
            else:
                for field_name, field_schema in properties.items():

                    if not isinstance(field_name, str) or not field_name:
                        errors.append(
                            f"{path} contains an invalid property name."
                        )
                        continue

                    result = self.validate_schema_definition(
                        field_schema,
                        f"{path}.properties.{field_name}",
                    )

                    errors.extend(result["errors"])

            additional = schema.get(
                "additional_properties",
                False,
            )

            if not isinstance(additional, bool):
                errors.append(
                    f"{path}.additional_properties must be a boolean."
                )

        if schema_type == "array":

            if "items" not in schema:
                errors.append(
                    f"{path}.items is required for array schemas."
                )
            else:
                result = self.validate_schema_definition(
                    schema["items"],
                    f"{path}.items",
                )
                errors.extend(result["errors"])

        if "enum" in schema:
            if not isinstance(schema["enum"], list):
                errors.append(f"{path}.enum must be a list.")
            elif not schema["enum"]:
                errors.append(f"{path}.enum cannot be empty.")

        for option in ("min", "max", "min_length", "max_length"):

            if option in schema:
                value = schema[option]

                if (
                    not isinstance(value, (int, float))
                    or isinstance(value, bool)
                ):
                    errors.append(
                        f"{path}.{option} must be a number."
                    )

                elif option in ("min_length", "max_length"):
                    if value < 0 or not isinstance(value, int):
                        errors.append(
                            f"{path}.{option} must be a "
                            "non-negative integer."
                        )

        if (
            "min" in schema
            and "max" in schema
            and schema["min"] > schema["max"]
        ):
            errors.append(
                f"{path}.min cannot be greater than {path}.max."
            )

        if (
            "min_length" in schema
            and "max_length" in schema
            and schema["min_length"] > schema["max_length"]
        ):
            errors.append(
                f"{path}.min_length cannot exceed max_length."
            )

        if "pattern" in schema:

            if not isinstance(schema["pattern"], str):
                errors.append(
                    f"{path}.pattern must be a string."
                )
            else:
                try:
                    re.compile(schema["pattern"])
                except re.error:
                    errors.append(
                        f"{path}.pattern is not a valid regular expression."
                    )

        if "description" in schema and not isinstance(
            schema["description"], str
        ):
            errors.append(
                f"{path}.description must be a string."
            )

        return {
            "valid": len(errors) == 0,
            "errors": errors,
        }

    # -----------------------------------------------------
    # REGISTER SCHEMAS
    # -----------------------------------------------------

    def register_schema(
        self,
        name: str,
        schema: Dict[str, Any],
        description: str = "",
        replace: bool = False,
    ) -> Dict[str, Any]:

        if not isinstance(name, str) or not name.strip():
            raise ValueError("A valid schema name is required.")

        name = name.strip()

        if name in self.schemas and not replace:
            raise APISchemaError(
                f"Schema '{name}' already exists."
            )

        if not isinstance(description, str):
            raise ValueError("Description must be a string.")

        validation = self.validate_schema_definition(schema)

        if not validation["valid"]:
            raise SchemaValidationError(
                "; ".join(validation["errors"])
            )

        self.schemas[name] = {
            "name": name,
            "description": description,
            "schema": copy.deepcopy(schema),
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
        }

        return {
            "success": True,
            "message": "Schema registered successfully.",
            "name": name,
        }

    # -----------------------------------------------------
    # RETRIEVE SCHEMAS
    # -----------------------------------------------------

    def get_schema(self, name: str) -> Dict[str, Any]:

        if name not in self.schemas:
            raise SchemaNotFoundError(
                f"Schema '{name}' was not found."
            )

        return copy.deepcopy(self.schemas[name])

    def list_schemas(self) -> List[Dict[str, Any]]:

        return [
            {
                "name": item["name"],
                "description": item["description"],
                "created_at": item["created_at"],
                "updated_at": item["updated_at"],
            }
            for item in self.schemas.values()
        ]

    # -----------------------------------------------------
    # TYPE CHECKING
    # -----------------------------------------------------

    @staticmethod
    def _matches_type(value: Any, expected_type: str) -> bool:

        if expected_type == "any":
            return True

        if expected_type == "string":
            return isinstance(value, str)

        if expected_type == "integer":
            return isinstance(value, int) and not isinstance(value, bool)

        if expected_type == "number":
            return (
                isinstance(value, (int, float))
                and not isinstance(value, bool)
            )

        if expected_type == "boolean":
            return isinstance(value, bool)

        if expected_type == "object":
            return isinstance(value, dict)

        if expected_type == "array":
            return isinstance(value, list)

        if expected_type == "date":
            if isinstance(value, datetime):
                return False

            if isinstance(value, date):
                return True

            if not isinstance(value, str):
                return False

            try:
                date.fromisoformat(value)
                return True
            except ValueError:
                return False

        if expected_type == "datetime":
            if isinstance(value, datetime):
                return True

            if not isinstance(value, str):
                return False

            try:
                datetime.fromisoformat(
                    value.replace("Z", "+00:00")
                )
                return True
            except ValueError:
                return False

        if expected_type == "email":
            if not isinstance(value, str):
                return False

            return bool(
                re.fullmatch(
                    r"[^@\s]+@[^@\s]+\.[^@\s]+",
                    value,
                )
            )

        if expected_type == "uuid":
            if not isinstance(value, str):
                return False

            pattern = (
                r"^[0-9a-fA-F]{8}-"
                r"[0-9a-fA-F]{4}-"
                r"[1-8][0-9a-fA-F]{3}-"
                r"[89abAB][0-9a-fA-F]{3}-"
                r"[0-9a-fA-F]{12}$"
            )

            return bool(re.fullmatch(pattern, value))

        return False

    # -----------------------------------------------------
    # VALIDATE INDIVIDUAL VALUES
    # -----------------------------------------------------

    def _validate_value(
        self,
        value: Any,
        schema: Dict[str, Any],
        path: str,
        errors: List[Dict[str, str]],
    ) -> None:

        if value is None:

            if schema.get("nullable", False):
                return

            errors.append({
                "field": path,
                "message": "This field cannot be null.",
            })
            return

        expected_type = schema["type"]

        if not self._matches_type(value, expected_type):

            errors.append({
                "field": path,
                "message": f"Expected type '{expected_type}'.",
            })
            return

        if "enum" in schema and value not in schema["enum"]:

            errors.append({
                "field": path,
                "message": "Value is not one of the allowed options.",
            })

        if expected_type in ("string", "email", "uuid"):

            if "min_length" in schema:
                if len(value) < schema["min_length"]:
                    errors.append({
                        "field": path,
                        "message": "Value is shorter than the minimum length.",
                    })

            if "max_length" in schema:
                if len(value) > schema["max_length"]:
                    errors.append({
                        "field": path,
                        "message": "Value exceeds the maximum length.",
                    })

            if "pattern" in schema:
                if not re.fullmatch(schema["pattern"], value):
                    errors.append({
                        "field": path,
                        "message": "Value does not match the required pattern.",
                    })

        if expected_type in ("integer", "number"):

            if "min" in schema and value < schema["min"]:
                errors.append({
                    "field": path,
                    "message": f"Value must be at least {schema['min']}.",
                })

            if "max" in schema and value > schema["max"]:
                errors.append({
                    "field": path,
                    "message": f"Value must not exceed {schema['max']}.",
                })

        if expected_type == "array":

            if "min" in schema and len(value) < schema["min"]:
                errors.append({
                    "field": path,
                    "message": "Array contains too few items.",
                })

            if "max" in schema and len(value) > schema["max"]:
                errors.append({
                    "field": path,
                    "message": "Array contains too many items.",
                })

            item_schema = schema["items"]

            for index, item in enumerate(value):

                self._validate_value(
                    item,
                    item_schema,
                    f"{path}[{index}]",
                    errors,
                )

        if expected_type == "object":

            properties = schema.get("properties", {})
            additional_allowed = schema.get(
                "additional_properties",
                False,
            )

            for field_name, field_schema in properties.items():

                if field_name not in value:

                    if field_schema.get("required", False):
                        errors.append({
                            "field": f"{path}.{field_name}",
                            "message": "Required field is missing.",
                        })

                    continue

                self._validate_value(
                    value[field_name],
                    field_schema,
                    f"{path}.{field_name}",
                    errors,
                )

            if not additional_allowed:

                unexpected = set(value.keys()) - set(properties.keys())

                for field_name in sorted(unexpected):

                    errors.append({
                        "field": f"{path}.{field_name}",
                        "message": "Unexpected field is not allowed.",
                    })

    # -----------------------------------------------------
    # VALIDATE DATA
    # -----------------------------------------------------

    def validate_data(
        self,
        data: Any,
        schema_name: str,
    ) -> Dict[str, Any]:

        registered = self.get_schema(schema_name)

        errors = []

        self._validate_value(
            data,
            registered["schema"],
            "data",
            errors,
        )

        return {
            "valid": len(errors) == 0,
            "schema_name": schema_name,
            "error_count": len(errors),
            "errors": errors,
        }

    def validate_or_raise(
        self,
        data: Any,
        schema_name: str,
    ) -> Dict[str, Any]:

        result = self.validate_data(data, schema_name)

        if not result["valid"]:
            raise APIDataValidationError(
                json.dumps(result["errors"], ensure_ascii=False)
            )

        return result

    # -----------------------------------------------------
    # UPDATE AND DELETE
    # -----------------------------------------------------

    def update_schema(
        self,
        name: str,
        schema: Dict[str, Any],
        description: Optional[str] = None,
    ) -> Dict[str, Any]:

        if name not in self.schemas:
            raise SchemaNotFoundError(
                f"Schema '{name}' was not found."
            )

        validation = self.validate_schema_definition(schema)

        if not validation["valid"]:
            raise SchemaValidationError(
                "; ".join(validation["errors"])
            )

        record = self.schemas[name]

        record["schema"] = copy.deepcopy(schema)
        record["updated_at"] = datetime.utcnow().isoformat()

        if description is not None:
            if not isinstance(description, str):
                raise ValueError("Description must be a string.")

            record["description"] = description

        return {
            "success": True,
            "message": "Schema updated successfully.",
            "name": name,
        }

    def delete_schema(self, name: str) -> Dict[str, Any]:

        if name not in self.schemas:
            raise SchemaNotFoundError(
                f"Schema '{name}' was not found."
            )

        del self.schemas[name]

        return {
            "success": True,
            "message": "Schema deleted successfully.",
            "name": name,
        }

    # -----------------------------------------------------
    # EXPORT
    # -----------------------------------------------------

    def export_schema(
        self,
        name: str,
        indent: int = 4,
    ) -> str:

        registered = self.get_schema(name)

        return json.dumps(
            registered,
            indent=indent,
            ensure_ascii=False,
        )

    def export_all_schemas(self) -> str:

        return json.dumps(
            self.schemas,
            indent=4,
            ensure_ascii=False,
        )


# ---------------------------------------------------------
# SHARED SERVICE INSTANCE
# ---------------------------------------------------------

api_schema_service = APISchemaService()


# ---------------------------------------------------------
# BASIC USAGE EXAMPLE
# ---------------------------------------------------------

if __name__ == "__main__":

    service = APISchemaService()

    employee_schema = {
        "type": "object",
        "properties": {
            "name": {
                "type": "string",
                "required": True,
                "min_length": 2,
                "max_length": 100,
            },
            "email": {
                "type": "email",
                "required": True,
            },
            "age": {
                "type": "integer",
                "required": True,
                "min": 18,
                "max": 100,
            },
            "department": {
                "type": "string",
                "required": True,
                "enum": [
                    "Computer Science",
                    "Accounting",
                    "Marketing",
                    "Production",
                ],
            },
            "skills": {
                "type": "array",
                "items": {
                    "type": "string",
                },
            },
        },
        "additional_properties": False,
    }

    service.register_schema(
        name="employee",
        schema=employee_schema,
        description="Employee registration schema.",
    )

    employee_data = {
        "name": "John Smith",
        "email": "john@example.com",
        "age": 25,
        "department": "Computer Science",
        "skills": ["Python", "SQL", "Excel"],
    }

    result = service.validate_data(
        employee_data,
        "employee",
    )

    print(json.dumps(result, indent=4))
