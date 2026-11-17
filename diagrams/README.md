# Atlas architecture diagrams

| Diagram | What it shows | Files |
|---|---|---|
| System overview | Browser, CloudFront, S3 images, VPC runtime, GitHub deployment and telemetry | `architecture.png`, `architecture.svg` |
| Network & security | Two Availability Zones, six CIDR blocks, ALB, private EC2, RDS, NAT and ports | `network.png`, `network.svg` |
| Activity pipeline | CloudWatch → Kinesis → Firehose/Lambda → S3 CSV → Athena, plus operational dashboard | `telemetry.png`, `telemetry.svg` |

PNG images are exported at 2200–2400 pixels wide. SVG is the preferred format for diagrams in documents and GitHub because it retains readable vector text when enlarged.

Regenerate PNG and SVG from `render_blueprints.py` using Python 3 plus `svgwrite` and `cairosvg`:

```bash
python -m pip install svgwrite cairosvg
python diagrams/render_blueprints.py
```

The legacy `.dot` files are reference alternatives to the current blueprints; their layout is not byte-for-byte identical to the new SVGs.

Security note: the demonstration profile allows CloudFront → ALB **HTTP 80**, while production-origin TLS requires domain and ACM certificate. The diagrams label both modes explicitly. CloudFront is outside the VPC, while the ALB occupies public subnets and EC2/RDS occupy private subnets.
