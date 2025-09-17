from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

"""
TESTS FOR CREATE USER
"""
def test_create_user():
    response = client.post("/v1/users", json={"email_address": "test@test.com"})
    assert response.status_code == 201
    assert response.json() == {"user_id": 1}

def test_create_user_with_existing_email():
    response = client.post("/v1/users", json={"email_address": "test@test.com"})
    assert response.status_code == 409
    assert response.json() == {"detail": "Email already exists"}

"""
TESTS FOR CREATE LOAN
"""
def test_create_loan(): 
    response = client.post("/v1/users/1/loans", json={"amount": 1000, "annual_interest_rate": 0.05, "loan_term_in_months": 12})
    assert response.status_code == 201
    assert response.json() == {"loan_id": 1, "owner_id": 1, "amount": 1000, "annual_interest_rate": 0.05, "loan_term_in_months": 12}

def test_create_loan_with_invalid_parameters():
    response = client.post("/v1/users/1/loans", json={"amount": -1000, "annual_interest_rate": 0.05, "loan_term_in_months": 12})
    assert response.status_code == 422
    assert response.json() == {"detail": "Invalid loan parameters"}

def test_create_loan_user_not_found():
    response = client.post("/v1/users/100/loans", json={"amount": 1000, "annual_interest_rate": 0.05, "loan_term_in_months": 12})
    assert response.status_code == 404
    assert response.json() == {"detail": "User with id 100 not found"}

"""
TESTS FOR GET LOANS
"""
def test_get_loans():
    response = client.get("/v1/users/1/loans")
    assert response.status_code == 200
    assert response.json() == {
    "loans": [
        {
            "loan_id": 1
        },
        {
            "loan_id": 2
        },
        {
            "loan_id": 3
        },
        {
            "loan_id": 4
        },
        {
            "loan_id": 5
        },
        {
            "loan_id": 6
        },
        {
            "loan_id": 7
        },
        {
            "loan_id": 8
        },
        {
            "loan_id": 9
        },
        {
            "loan_id": 10
        }
    ],
    "offset": 10
}

def test_get_loans_when_user_id_not_found():
    response = client.get("/v1/users/100/loans")
    assert response.status_code == 404
    assert response.json() == {"detail": "User with id 100 not found"}

def test_pagination_and_get_next_page():
    response = client.get("/v1/users/1/loans?limit=10&offset=0")
    assert response.status_code == 200
    assert response.json() == {
        "loans": [
            {
                "loan_id": 1
            },
            {
                "loan_id": 2
            },
            {
                "loan_id": 3
            },
            {
                "loan_id": 4
            },
            {
                "loan_id": 5
            },
            {
                "loan_id": 6
            },
            {
                "loan_id": 7
            },
            {
                "loan_id": 8
            },
            {
                "loan_id": 9
            },
            {
                "loan_id": 10
            }
        ],
        "offset": 10
    }
    response = client.get("/v1/users/1/loans?limit=10&offset=10")
    assert response.status_code == 200
    assert response.json() == {
        "loans": [
            {
                "loan_id": 11
            },
            {
                "loan_id": 12
            },
            {
                "loan_id": 13
            },
            {
                "loan_id": 14
            },
            {
                "loan_id": 15
            },
            {
                "loan_id": 16
            },
            {
                "loan_id": 17
            },
            {
                "loan_id": 18
            },
            {
                "loan_id": 19
            },
            {
                "loan_id": 20
            }
        ],
        "offset": 20
    }

"""
TESTS FOR LOAN SHARING
"""
def test_share_loan():
    response = client.patch("/v1/users/1/loans/11/share/2")
    assert response.status_code == 200
    assert response.json() == {
        "loan_id": 4,
        "shared_with": {
            "user_ids": [
                2
            ]
        }
    }

def test_share_loan_when_user_is_already_shared():
    response = client.patch("/v1/users/1/loans/1/share/1")
    assert response.status_code == 400
    assert response.json() == {"detail": "User is already shared or is the loan owner"}

def test_share_loan_when_loan_id_not_found():
    response = client.patch("/v1/users/1/loans/100/share/2")
    assert response.status_code == 404
    assert response.json() == {"detail": "Loan with id 100 not found"}

def test_share_loan_when_user_is_not_the_loan_owner():
    response = client.patch("/v1/users/2/loans/20/share/1")
    assert response.status_code == 403
    assert response.json() == {"detail": "You do not have permission to share this loan"}

def test_share_loan_when_user_id_not_found():
    response = client.patch("/v1/users/100/loans/20/share/2")
    assert response.status_code == 403
    assert response.json() == {"detail": "You do not have permission to share this loan"}

def test_share_loan_when_shared_with_user_id_not_found():
    response = client.patch("/v1/users/1/loans/20/share/100")
    assert response.status_code == 404
    assert response.json() == {"detail": "User with id 100 not found"}

"""
TESTS FOR LOAN SCHEDULE
"""
def test_get_loan_schedule():
    response = client.get("/v1/users/1/loans/1/schedule")
    assert response.status_code == 200
    assert response.json() == {
        "schedule": [
            {
                "month": 1,
                "monthly_payment": 85.61,
                "remaining_balance": 918.56
            },
            {
                "month": 2,
                "monthly_payment": 85.61,
                "remaining_balance": 836.78
            },
            {
                "month": 3,
                "monthly_payment": 85.61,
                "remaining_balance": 754.66
            },
            {
                "month": 4,
                "monthly_payment": 85.61,
                "remaining_balance": 672.2
            },
            {
                "month": 5,
                "monthly_payment": 85.61,
                "remaining_balance": 589.39
            },
            {
                "month": 6,
                "monthly_payment": 85.61,
                "remaining_balance": 506.24
            },
            {
                "month": 7,
                "monthly_payment": 85.61,
                "remaining_balance": 422.74
            },
            {
                "month": 8,
                "monthly_payment": 85.61,
                "remaining_balance": 338.89
            },
            {
                "month": 9,
                "monthly_payment": 85.61,
                "remaining_balance": 254.7
            },
            {
                "month": 10,
                "monthly_payment": 85.61,
                "remaining_balance": 170.15
            },
            {
                "month": 11,
                "monthly_payment": 85.61,
                "remaining_balance": 85.25
            },
            {
                "month": 12,
                "monthly_payment": 85.61,
                "remaining_balance": 0
            }
        ]
    }

def test_get_loan_summary_when_not_shared_with_user():
    response = client.get("/v1/users/100/loans/1/schedule/10")
    assert response.status_code == 404
    assert response.json() == {"detail": "User with id 100 not found"}

def test_get_loan_schedule_with_invalid_loan_id():
    response = client.get("/v1/users/1/loans/100/schedule")
    assert response.status_code == 404
    assert response.json() == {"detail": "Loan with id 100 not found"}

"""
TESTS FOR LOAN SUMMARY
"""
def test_get_loan_summary(): 
    response = client.get("/v1/users/1/loans/1/schedule/10")
    assert response.status_code == 200
    assert response.json() == {
        "loan_id": 1,
        "month": 10,
        "principal_balance": 170.15,
        "aggregate_principal_paid": 829.85,
        "aggregate_interest_paid": 26.23
    }

def test_get_loan_summary_when_not_shared_with_user():
    response = client.get("/v1/users/3/loans/10/schedule/10")
    assert response.status_code == 403
    assert response.json() == {"detail": "Loan is not shared with user"}

def test_get_loan_summary_with_invalid_month():
    response = client.get("/v1/users/1/loans/1/schedule/13")
    assert response.status_code == 422
    assert response.json() == {"detail": "Month must be between 1 and 12"}

def test_get_loan_summary_with_invalid_loan_id():
    response = client.get("/v1/users/1/loans/100/schedule/10")
    assert response.status_code == 404
    assert response.json() == {"detail": "Loan with id 100 not found"}