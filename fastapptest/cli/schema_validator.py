# cli/schema_validator.py

from typing import List, Dict, Optional
from pydantic import BaseModel
from fastapptest.core.validators import Validator

class SchemaValidator:
    """
    CLI-facing schema validator.
    Can validate single response or a batch of responses against Pydantic models.
    """

    @staticmethod
    def validate_response(
        response: Dict,
        model: Optional[BaseModel] = None,
        expected_status: int = 200,
        required_fields: Optional[List[str]] = None
    ) -> Dict[str, str]:
        """
        Validate a single API response.
        Returns dictionary with passed/error details.
        """
        return Validator.validate(
            response,
            expected_status=expected_status,
            model=model,
            required_fields=required_fields
        )

    @staticmethod
    def validate_batch(
        responses: Dict[str, Dict],
        models: Dict[str, BaseModel],
        expected_status: int = 200
    ) -> Dict[str, Dict]:
        """
        Validate multiple responses in a batch.
        `responses` = {"GET /users": {...}, "POST /users": {...}}
        `models` = {"GET /users": UserOut, "POST /users": UserOut}
        """
        results = {}
        for key, resp in responses.items():
            model = models.get(key)
            results[key] = Validator.validate(
                resp,
                expected_status=expected_status,
                model=model
            )
        return results
