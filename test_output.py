from output_generators import OutputGenerator

# Test the output generators
generator = OutputGenerator()

print("Generating Markdown output...")
md_file = generator.generate_markdown()
print(f"Markdown file created: {md_file}")

print("\nGenerating HTML output...")
html_file = generator.generate_html()
print(f"HTML file created: {html_file}")

print("\nOutput generation test complete!")