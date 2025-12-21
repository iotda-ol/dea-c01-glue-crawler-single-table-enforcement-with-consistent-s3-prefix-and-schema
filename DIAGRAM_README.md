# Infrastructure Diagram Files - Quick Start

## 📊 Files Overview

This repository includes a comprehensive universal infrastructure diagram system for multi-cloud data catalog and ETL architecture.

### Main Diagram File

**📄 map-diagram-infra.mermaid** (13 KB, 306 lines)
- Format: Mermaid diagram language
- Extension: `.mermaid` for universal compatibility
- Universal architecture mapping for AWS, GCP, and Azure
- Includes extensive inline documentation and annotations

## 🚀 Quick Start - How to View the Diagram

### Option 1: GitHub (Easiest)
1. View `DIAGRAM_PREVIEW.md` on GitHub - Mermaid renders automatically
2. Or view `map-diagram-infra.mermaid` directly on GitHub

### Option 2: Interactive HTML Viewer (Best Visual Experience)
1. Open `diagram-viewer.html` in any web browser
2. No installation required
3. Fully styled with colors and interactive elements

### Option 3: Mermaid Live Editor (For Editing)
1. Go to https://mermaid.live/
2. Copy contents of `map-diagram-infra.mermaid`
3. Paste into editor
4. Export as PNG, SVG, or PDF

### Option 4: VS Code (For Development)
1. Install extension: "Markdown Preview Mermaid Support"
2. Open `DIAGRAM_PREVIEW.md`
3. Press Ctrl+Shift+V (Windows/Linux) or Cmd+Shift+V (Mac)

### Option 5: Command Line Export
```bash
# Install mermaid-cli globally
npm install -g @mermaid-js/mermaid-cli

# Generate PNG
mmdc -i map-diagram-infra.mermaid -o map-diagram-infra.png

# Generate SVG
mmdc -i map-diagram-infra.mermaid -o map-diagram-infra.svg

# Generate PDF
mmdc -i map-diagram-infra.mermaid -o map-diagram-infra.pdf
```

## 📚 Documentation Files

### 1. INFRASTRUCTURE_DIAGRAM.md (11 KB)
**Comprehensive guide covering:**
- Complete viewing instructions
- Component descriptions for all 20+ services
- Critical configuration requirements
- IaC examples (Terraform, Pulumi, etc.)
- Cost comparisons
- Migration paths between clouds

### 2. CLOUD_MAPPING_REFERENCE.md (7.3 KB)
**Quick reference card with:**
- Service mapping tables
- Cost comparison charts
- Migration strategies
- Best practices checklist
- Critical configuration summary

### 3. DIAGRAM_PREVIEW.md (6 KB)
**GitHub-optimized preview:**
- Embedded Mermaid diagram
- Component mapping legend
- Key features summary
- Quick viewing instructions

### 4. diagram-viewer.html (11 KB)
**Interactive browser viewer:**
- Styled diagram with colors
- Component legend
- Bootstrap-inspired design
- No dependencies required

## 🌐 Cloud Coverage

### AWS (Amazon Web Services)
- ✅ S3, Glue Data Catalog, Glue Crawler
- ✅ IAM Roles, Athena, EMR, Redshift Spectrum
- ✅ CloudWatch, CloudTrail, VPC Endpoints

### GCP (Google Cloud Platform)
- ✅ Cloud Storage, Dataplex, Data Catalog
- ✅ Service Accounts, BigQuery, Dataproc
- ✅ Cloud Logging, Cloud Monitoring, Audit Logs

### Azure (Microsoft Azure)
- ✅ Blob Storage, Purview, Data Factory
- ✅ Managed Identities, Synapse, Databricks
- ✅ Azure Monitor, Activity Log, Private Endpoints

## 🎯 Key Diagram Features

### Architecture Components (7 Major Groups)
1. **Object Storage Layer** - S3, Cloud Storage, Blob Storage
2. **Data Catalog Layer** - Glue, Dataplex, Purview
3. **Schema Discovery & ETL** - Crawlers and discovery services
4. **Identity & Access Management** - Roles and permissions
5. **Observability** - Logging, monitoring, audit trails
6. **Query & Analytics** - SQL engines and analytics platforms
7. **Security Controls** - Network security and compliance

### Visual Elements
- 🎨 Color-coded components by function
- ➡️ Data flow arrows showing relationships
- 📦 Nested subgraphs for organization
- 🏷️ Multi-line labels with cloud provider mappings

### Documentation Sections
- Component mapping table
- Critical configuration for single table enforcement
- IaC provider support (Terraform, Pulumi, CloudFormation, etc.)
- Cost comparison across clouds
- Migration paths between providers
- Best practices (universal across all clouds)

## 🔑 Critical Configuration Highlights

### Single Table Enforcement (Universal Pattern)
```
✅ CORRECT:
   storage://bucket/third-party-data/file1.csv
   storage://bucket/third-party-data/file2.csv

❌ WRONG (creates multiple tables):
   storage://bucket/data/2024/01/file1.csv
   storage://bucket/vendor-a/file1.csv
```

### Schema Merge Policy
- **AWS**: `CombineCompatibleSchemas` + `MergeNewColumns`
- **GCP**: Schema evolution enabled in Dataplex
- **Azure**: Schema drift handling in Purview scan rules

### Similarity Threshold
- **0.7** - Aggressive grouping (more files in one table)
- **0.8** - Balanced (recommended)
- **0.9** - Conservative (strict matching)

## 📦 File Sizes

| File | Size | Lines | Purpose |
|------|------|-------|---------|
| map-diagram-infra.mermaid | 13 KB | 306 | Main diagram source |
| INFRASTRUCTURE_DIAGRAM.md | 11 KB | 407 | Complete guide |
| diagram-viewer.html | 11 KB | 283 | Interactive viewer |
| CLOUD_MAPPING_REFERENCE.md | 7.3 KB | 253 | Quick reference |
| DIAGRAM_PREVIEW.md | 6 KB | 131 | GitHub preview |

## 🛠️ Customization

To customize the diagram:
1. Edit `map-diagram-infra.mermaid`
2. Test changes at https://mermaid.live/
3. Update documentation files if adding components
4. Regenerate exports (PNG/SVG/PDF) if needed

## 💡 Tips

- **For presentations**: Use `diagram-viewer.html` or export to PNG/SVG
- **For documentation**: Link to `INFRASTRUCTURE_DIAGRAM.md`
- **For quick reference**: Use `CLOUD_MAPPING_REFERENCE.md`
- **For GitHub README**: Embed from `DIAGRAM_PREVIEW.md`
- **For editing**: Use Mermaid Live Editor or VS Code

## 📖 Related Documentation

- [Main README](README.md) - Project overview
- [Architecture](docs/ARCHITECTURE.md) - AWS-specific architecture
- [Setup Guide](docs/SETUP.md) - Deployment instructions
- [Best Practices](docs/DEA_C01_BEST_PRACTICES.md) - AWS certification prep

## ✨ What Makes This Diagram "Universal"?

1. **Multi-Cloud Mapping**: Every component shows AWS, GCP, and Azure equivalents
2. **Cloud-Agnostic Patterns**: Best practices applicable to all platforms
3. **Migration Paths**: Clear guidance for moving between clouds
4. **IaC Support**: Examples for Terraform, Pulumi, and native tools
5. **Cost Transparency**: Price comparisons across providers
6. **Vendor-Neutral Language**: Universal terminology with cloud-specific mappings

## 🎓 Use Cases

- **Learning**: Understand equivalent services across clouds
- **Migration**: Plan transitions between cloud providers
- **Architecture Reviews**: Present multi-cloud capabilities
- **Documentation**: Include in project documentation
- **Training**: Teach cloud architecture concepts
- **Certification Prep**: DEA-C01 and multi-cloud certifications

---

**📊 Version**: 1.0  
**📅 Created**: 2025-12-21  
**🔧 Maintained By**: Project Contributors  
**📝 License**: MIT (same as repository)
