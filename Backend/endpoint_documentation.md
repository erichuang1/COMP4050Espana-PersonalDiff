Base URL: http://13.239.27.195/ 
# Unit Management: 
## Create a New Unit

### Endpoint: `/units`  
### Request type : `POST`
- Example URL to send request to this endpoint:`http://13.239.27.195/units`

### Description:
- Creates a new unit requested by a convener.
### Path Parameters: 
- None
### Request Headers:

| Header       | Value              |
|--------------|--------------------|
| `Content-Type` | `application/json` |

### Request Body (JSON):
```json
{
  "unit_code": "COMP1350",
  "unit_name": "Introduction to Database Management Systems",
  "convener_id": 1,
  "year": 2024,
  "session": "2"
}
```

### Possible Responses from Backend:

1. **`Status: 200 OK`**
- Response Body: 
    ```json
    {
    "convener_id": 1,
    "session": "2",
    "unit_code": "COMP1350",
    "unit_name": "Introduction to Database Management Systems",
    "year": 2024
    }
    ```
2. **`Status: 404 Bad Request`**
-  Response Body:
    ```json
    {
    "message": "Unit not found"
    }
    ```

## Retrieve a particular unit 
### Endpoint: `/units/<string:unit_code>`  
- Example URL to send request to this endpoint:`http://13.239.27.195/units/COMP1350`
### Request type : `GET`

### Description:
- Retrieves the details particular unit from the database 
### Path Parameters: 
1. `unit_code`: (string): The code of the unit 
### Request Headers:

| Header       | Value              |
|--------------|--------------------|
| `Content-Type` | `application/json` |

### Possible Responses from Backend:

1. **`Status: 200 OK`**
- Response Body:
    ```json
    {
    "convener_id": 1,
    "session": "2",
    "unit_code": "COMP1350",
    "unit_name": "Introduction to Database Management Systems",
    "year": 2024
    }
    ```
2. **`Status: 404 Bad Request`**
-  Response Body:
    ```json
    {
    "message": "Unit not found"
    }
    ```




