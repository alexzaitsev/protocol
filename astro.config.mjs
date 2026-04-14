import { defineConfig } from 'astro/config';
import starlight from '@astrojs/starlight';

export default defineConfig({
  site: 'https://alexzaitsev.github.io',
  base: '/protocol',
  srcDir: './docs',
  markdown: {
    smartypants: false,
  },
  integrations: [
    starlight({
      title: 'Protocol',
      description:
        'Supplement protocol management engine with biomarker correlation, temporal versioning, and an AI-first interface.',
      customCss: ['./docs/styles/landing.css'],
      social: [
        {
          icon: 'github',
          label: 'GitHub',
          href: 'https://github.com/alexzaitsev/protocol',
        },
      ],
      editLink: {
        baseUrl: 'https://github.com/alexzaitsev/protocol/edit/main/',
      },
      sidebar: [
        { label: 'Home', slug: 'index' },
        {
          label: 'Guides',
          items: [
            { slug: 'guides/introduction' },
            {
              label: 'Prerequisites',
              items: [
                { label: 'Overview', slug: 'guides/prerequisites' },
                { slug: 'guides/prerequisites/supabase' },
                { slug: 'guides/prerequisites/google-cloud' },
                { slug: 'guides/prerequisites/fly' },
              ],
            },
            { slug: 'guides/deployment' },
            { slug: 'guides/onboarding' },
            { slug: 'guides/usage-examples' },
          ],
        },
        {
          label: 'Development',
          items: [
            { label: 'Development', slug: 'development/development' },
            {
              label: 'Architecture',
              items: [
                { slug: 'development/architecture/overview' },
                { slug: 'development/architecture/data-layer' },
              ],
            },
            {
              label: 'Database',
              items: [
                { slug: 'development/database/schema' },
                { label: 'RLS Policies', slug: 'development/database/rls' },
              ],
            },
            {
              label: 'MCP Server',
              items: [
                { label: 'MCP Tools', slug: 'development/mcp-server/mcp-tools' },
              ],
            },
          ],
        },
        {
          label: 'Roadmap',
          items: [{ slug: 'roadmap/roadmap' }],
        },
      ],
    }),
  ],
});
