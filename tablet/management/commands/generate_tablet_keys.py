from django.core.management.base import BaseCommand
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization


class Command(BaseCommand):
    help = "RSA-2048 kalit juftini yaratadi va .env uchun chop etadi"

    def handle(self, *args, **options):
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
        )

        private_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        ).decode()

        public_pem = private_key.public_key().public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        ).decode()

        private_oneline = private_pem.replace('\n', '\\n')

        self.stdout.write(self.style.SUCCESS("=== .env ga qo'shing ==="))
        self.stdout.write(f'TABLET_RSA_PRIVATE_KEY="{private_oneline}"')
        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("=== Planshetga bering (ochiq kalit) ==="))
        self.stdout.write(public_pem)
