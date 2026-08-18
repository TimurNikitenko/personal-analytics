from datetime import date
import pytest
from backend.app.schemas import FinanceCreate
from backend.app.core.exceptions import EntityNotFoundException
from backend.app.domains.finances.service import FinancesService

class MockFinanceRepo:
    def __init__(self):
        self.entries = {}

    def list_entries(self, start_date=None, end_date=None):
        return list(self.entries.values())

    def create_entry(self, finance_in: FinanceCreate):
        class DummyFinance:
            def __init__(self, fid, d, amount, category, ftype):
                self.id = fid
                self.date = d
                self.amount = amount
                self.category = category
                self.transaction_type = ftype

        fid = len(self.entries) + 1
        obj = DummyFinance(fid, finance_in.date, finance_in.amount, finance_in.category, finance_in.transaction_type)
        self.entries[fid] = obj
        return obj

    def bulk_create_entries(self, finance_ins):
        return [self.create_entry(e) for e in finance_ins]

    def delete_entry(self, finance_id: int):
        if finance_id in self.entries:
            del self.entries[finance_id]
            return True
        return False

def test_finances_service_totals():
    repo = MockFinanceRepo()
    service = FinancesService(repo)

    e1 = FinanceCreate(date=date(2026, 8, 18), amount=1000.0, category="Salary", transaction_type="income")
    e2 = FinanceCreate(date=date(2026, 8, 18), amount=200.0, category="Groceries", transaction_type="expense")
    e3 = FinanceCreate(date=date(2026, 8, 18), amount=300.0, category="ETF", transaction_type="saving")

    service.bulk_create_entries([e1, e2, e3])
    entries = service.list_entries()
    assert len(entries) == 3

    totals = service.calculate_totals(entries)
    assert totals["income"] == 1000.0
    assert totals["expense"] == 200.0
    assert totals["saving"] == 300.0
    assert totals["net_flow"] == 500.0
