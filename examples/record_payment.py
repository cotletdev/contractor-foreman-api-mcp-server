#!/usr/bin/env python3
"""Record a check or transfer against a Contractor Foreman invoice, found by its number.

    python record_payment.py --invoice 11 --amount 500 --method check --notes "Check #1042"
    python record_payment.py --invoice 11 --amount 500 --method check --dry-run

The amount may not exceed the balance due. Prints the new balance.
"""

from __future__ import annotations

import argparse

from contractor_foreman_api_mcp.scripting import call, paginate, run


def main() -> None:
    parser = argparse.ArgumentParser(description=(__doc__ or "").splitlines()[0])
    parser.add_argument("--invoice", required=True, help="Invoice number as shown in the app")
    parser.add_argument("--amount", type=float, required=True)
    parser.add_argument("--method", choices=["bank_transfer", "cash", "check", "credit_card", "other"], required=True)
    parser.add_argument("--date", help="Payment date, YYYY-MM-DD (default: today)")
    parser.add_argument("--notes", help="e.g. the check number")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    matches = [
        i
        for i in paginate("list_invoices", {"search": args.invoice, "limit": 100}, "invoices")
        if i["number"] == args.invoice
    ]
    if len(matches) != 1:
        raise SystemExit(f"Found {len(matches)} invoices numbered {args.invoice}.")
    invoice = matches[0]
    print(f"Invoice #{invoice['number']}, {invoice['customer_name']}: balance {invoice['balance_due']:,.2f}")
    if args.dry_run:
        return
    payment = call(
        "record_payment",
        {
            "invoice_id": invoice["invoice_id"],
            "amount": args.amount,
            "method": args.method,
            "date": args.date,
            "notes": args.notes,
        },
    )
    print(f"Payment {payment['payment_id']} recorded, balance now {payment['balance_due']:,.2f}")


if __name__ == "__main__":
    run(main)
