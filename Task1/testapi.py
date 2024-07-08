from flask import Flask, jsonify, request

app = Flask(__name__)

# Example data
emails_tables = {
    'ddw@arpnewsletters.com': ['Recipient Not Found', 'Unsubscribe'],
    'aanp@arpnewsletters.com': ['Recipient Not Found'],
    'txoga@arpnewsletters.com': ['Recipient Not Found', 'TXOGA Review']
}

filters = {
    'Recipient Not Found': [
        {'email': 'ddw@arpnewsletters.com', 'tables': ['Recipient Not Found']},
        {'email': 'aanp@arpnewsletters.com', 'tables': ['Recipient Not Found']},
        {'email': 'txoga@arpnewsletters.com', 'tables': ['Recipient Not Found', 'TXOGA Review']}
    ]
}

@app.route('/api/filters', methods=['GET'])
def get_filters():
    return jsonify(filters)

@app.route('/api/emails', methods=['GET'])
def get_emails():
    return jsonify(emails_tables)

@app.route('/api/filters', methods=['POST'])
def create_filter():
    new_filter = request.json
    filter_name = new_filter.get('filter_name')
    email = new_filter.get('email')
    table = new_filter.get('table')
    
    if filter_name and email and table:
        if filter_name not in filters:
            filters[filter_name] = []
        filters[filter_name].append({'email': email, 'tables': [table]})
        return jsonify({'message': 'Filter created successfully'}), 201
    else:
        return jsonify({'message': 'Invalid input'}), 400

@app.route('/api/emails', methods=['POST'])
def add_email():
    new_email = request.json
    email = new_email.get('email')
    tables = new_email.get('tables')
    
    if email and tables:
        emails_tables[email] = tables
        return jsonify({'message': 'Email and tables added successfully'}), 201
    else:
        return jsonify({'message': 'Invalid input'}), 400

if __name__ == '__main__':
    app.run(debug=True)
