import unittest
from types import SimpleNamespace
from unittest.mock import patch

from backend.app import main as backend_main
from frontend.app import main as frontend_main


class BackendTests(unittest.TestCase):
    def test_healthcheck(self):
        self.assertEqual(backend_main.healthcheck(), {"status": "ok"})

    def test_invoice_contains_consistent_totals(self):
        invoice = backend_main.get_factura("TEST-001")

        self.assertEqual(invoice["numero_factura"], "TEST-001")
        self.assertGreaterEqual(len(invoice["detalle"]), 1)
        self.assertAlmostEqual(
            invoice["subtotal"] + invoice["impuesto"],
            invoice["total"],
            places=2,
        )
        self.assertAlmostEqual(
            sum(item["total"] for item in invoice["detalle"]),
            invoice["subtotal"],
            places=2,
        )


class FrontendTests(unittest.TestCase):
    def setUp(self):
        self.client = frontend_main.app.test_client()
        self.invoice = {
            "numero_factura": "TEST-001",
            "fecha_emision": "2026-11-15",
            "empresa": {
                "nombre": "Empresa Demo",
                "direccion": "Calle 1",
                "telefono": "123",
                "email": "demo@example.com",
            },
            "cliente": {
                "nombre": "Cliente Demo",
                "direccion": "Calle 2",
                "telefono": "456",
            },
            "detalle": [
                {
                    "descripcion": "Servicio",
                    "cantidad": 2,
                    "precio_unitario": 10.0,
                    "total": 20.0,
                }
            ],
            "subtotal": 20.0,
            "impuesto": 4.2,
            "total": 24.2,
        }

    def test_empty_invoice_id_returns_bad_request(self):
        response = self.client.post("/generar-pdf", data={"id_factura": " "})

        self.assertEqual(response.status_code, 400)

    @patch.object(frontend_main.requests, "get")
    def test_invoice_request_returns_pdf(self, mock_get):
        mock_get.return_value = SimpleNamespace(
            status_code=200,
            json=lambda: self.invoice,
        )

        response = self.client.post(
            "/generar-pdf",
            data={"id_factura": "TEST-001"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.mimetype, "application/pdf")
        self.assertTrue(response.data.startswith(b"%PDF"))
        self.assertIn("factura-TEST-001.pdf", response.headers["Content-Disposition"])


if __name__ == "__main__":
    unittest.main()
