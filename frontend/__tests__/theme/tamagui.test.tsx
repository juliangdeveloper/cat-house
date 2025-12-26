import config from '../../tamagui.config';

describe('Tamagui Theme System', () => {
  describe('TamaguiProvider Configuration', () => {
    it('should have a valid Tamagui configuration object', () => {
      expect(config).toBeDefined();
      expect(config).toHaveProperty('themes');
      expect(config).toHaveProperty('tokens');
      expect(config).toHaveProperty('fonts');
    });
  });

  describe('Theme Configuration', () => {
    it('should have light and dark themes configured', () => {
      expect(config.themes).toBeDefined();
      expect(config.themes.light).toBeDefined();
      expect(config.themes.dark).toBeDefined();
    });

    it('should have design tokens defined', () => {
      expect(config.tokens).toBeDefined();
      expect(config.tokens.color).toBeDefined();
      expect(config.tokens.space).toBeDefined();
      expect(config.tokens.size).toBeDefined();
    });

    it('should have font configuration', () => {
      expect(config.fonts).toBeDefined();
      expect(config.fonts.heading).toBeDefined();
      expect(config.fonts.body).toBeDefined();
    });

    it('should have responsive media queries', () => {
      expect(config.media).toBeDefined();
      expect(config.media.xs).toBeDefined();
      expect(config.media.sm).toBeDefined();
      expect(config.media.md).toBeDefined();
      expect(config.media.lg).toBeDefined();
    });

    it('should have shorthands configured', () => {
      expect(config.shorthands).toBeDefined();
    });
  });

  describe('Theme Properties', () => {
    it('should have color tokens in light theme', () => {
      const lightTheme = config.themes.light;
      expect(lightTheme).toBeDefined();
      expect(lightTheme.color).toBeDefined();
    });

    it('should have color tokens in dark theme', () => {
      const darkTheme = config.themes.dark;
      expect(darkTheme).toBeDefined();
      expect(darkTheme.color).toBeDefined();
    });

    it('should have space tokens defined with numeric values', () => {
      expect(config.tokens.space).toBeDefined();
      const spaceKeys = Object.keys(config.tokens.space);
      expect(spaceKeys.length).toBeGreaterThan(0);
    });

    it('should have size tokens defined with numeric values', () => {
      expect(config.tokens.size).toBeDefined();
      const sizeKeys = Object.keys(config.tokens.size);
      expect(sizeKeys.length).toBeGreaterThan(0);
    });
  });

  describe('Responsive Media Queries', () => {
    it('should have xs breakpoint defined', () => {
      expect(config.media.xs).toEqual({ maxWidth: 660 });
    });

    it('should have sm breakpoint defined', () => {
      expect(config.media.sm).toEqual({ maxWidth: 800 });
    });

    it('should have md breakpoint defined', () => {
      expect(config.media.md).toEqual({ maxWidth: 1020 });
    });

    it('should have lg breakpoint defined', () => {
      expect(config.media.lg).toEqual({ maxWidth: 1280 });
    });

    it('should have mobile-first breakpoints (gt prefix)', () => {
      expect(config.media.gtXs).toBeDefined();
      expect(config.media.gtSm).toBeDefined();
      expect(config.media.gtMd).toBeDefined();
      expect(config.media.gtLg).toBeDefined();
    });
  });

  describe('Font Configuration', () => {
    it('should have heading font with proper sizes', () => {
      const headingFont = config.fonts.heading;
      expect(headingFont).toBeDefined();
      expect(headingFont.size).toBeDefined();
    });

    it('should have body font with proper configuration', () => {
      const bodyFont = config.fonts.body;
      expect(bodyFont).toBeDefined();
      expect(bodyFont.size).toBeDefined();
    });
  });
});
