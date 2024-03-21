# Backend Overview

## Notes

### Questions

- Can ChatGPT be used to summarize and recommend? Example prompt:

  > A "website shape" describes how the structural elements of a website come together to effectively deliver content to a user.
  > Elements of "website shape" include top navigation bars, footers with summary links, single-column layouts on blog posts, and more.
  > What "website shape" would you recommend for a CATEGORY site that focuses on the keywords KEYWORD, KEYWORD, and KEYWORD?

- How do we represent color data? Maybe a stackable set of circles with borders that are a lightened/darkened version of the color?

### Interesting Website Data

There are many features of a website that are interesting to track over time.

- **Dominant site colors:** Background, foreground, theme palette.
- **Favicon colors:** Same as above but smaller palette size.
- **Fonts:** breakdown of fonts used by various HTML elements.
- **Shape:** Header, footer, single-column, sidebar, etc. Extracting these features seems nontrivial.

A screenshot will serve most of these needs, but it would be interesting and useful to also extract features based on the rendered HTML and CSS.

#### Data and Storage

- Apparently using the [CIELAB color space](https://en.wikipedia.org/wiki/CIELAB_color_space) will let us compute relative distances between any two colors. Backing this with PostgreSQL+PostGIS will let us efficiently query for color similarities.

## Use Cases

### Admin requests one-time scraping

### Admin registers new site for regular scraping

### Admin registers backfill for a single site

### User views timeline of all sites that have used a specific color

### User views results of a specific scraping job

### User views summary of all data for single site

### User views summary of all data for single category

### User compares results (similarities) between two sites

### User wants to create a site matching a category and time and keywords.

The system will generate a compatible color palette and website "shape"
