from flask import Flask, request, jsonify

app = Flask(__name__)

# Dummy data that mimics the expected response
dummy_response = [
    {
        "0": "ddw@arpnewsletters.com",
        "filterData": [
            {
                "id": 1,
                "emailId": 1,
                "filterId": 1,
                "tableId": 1,
                "is_active": 1,
                "deleted_at": None,
                "created_at": "2024-07-02T09:49:23.000000Z",
                "updated_at": "2024-07-02T09:49:23.000000Z",
                "tableInfo": {
                    "id": 1,
                    "tableName": "Recipient Not Found"
                },
                "filterInfo": {
                    "id": 1,
                    "filterName": "Recipient Not Found",
                    "filterOnSubject": 1,
                    "filterOnBody": 1,
                    "is_active": 1
                }
            },
            {
                "id": 2,
                "emailId": 1,
                "filterId": 1,
                "tableId": 2,
                "is_active": 1,
                "deleted_at": None,
                "created_at": "2024-07-02T09:49:23.000000Z",
                "updated_at": "2024-07-02T09:49:23.000000Z",
                "tableInfo": {
                    "id": 2,
                    "tableName": "Unsubscribe"
                },
                "filterInfo": {
                    "id": 1,
                    "filterName": "Recipient Not Found",
                    "filterOnSubject": 1,
                    "filterOnBody": 1,
                    "is_active": 1
                }
            }
        ]
    }
]

@app.route('/api/get-filter', methods=['POST'])
def dummy_post_endpoint():
    if request.method == 'POST':
        data = request.get_json()
        email_list = data.get('emailList', [])

        # Dummy response always returns the same data
        return jsonify(dummy_response)

if __name__ == '__main__':
    app.run(debug=True)
