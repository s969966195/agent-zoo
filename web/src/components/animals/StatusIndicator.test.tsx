import { render, screen } from '@testing-library/react';
import { StatusIndicator } from './StatusIndicator';

describe('StatusIndicator', () => {
  it('should render with correct color for available status', () => {
    render(<StatusIndicator status="available" />);
    const indicator = screen.getByTitle('在线');
    expect(indicator).toBeInTheDocument();
    expect(indicator).toHaveStyle({ backgroundColor: '#00E676' });
  });

  it('should render with correct color for busy status', () => {
    render(<StatusIndicator status="busy" />);
    const indicator = screen.getByTitle('忙碌');
    expect(indicator).toBeInTheDocument();
    expect(indicator).toHaveStyle({ backgroundColor: '#FFB74D' });
  });

  it('should render with correct color for offline status', () => {
    render(<StatusIndicator status="offline" />);
    const indicator = screen.getByTitle('离线');
    expect(indicator).toBeInTheDocument();
    expect(indicator).toHaveStyle({ backgroundColor: '#9E9E9E' });
  });

  it('should render with default size (md)', () => {
    render(<StatusIndicator status="available" />);
    const indicator = screen.getByTitle('在线');
    expect(indicator).toHaveClass('w-3', 'h-3');
  });

  it('should render with sm size', () => {
    render(<StatusIndicator status="available" size="sm" />);
    const indicator = screen.getByTitle('在线');
    expect(indicator).toHaveClass('w-2.5', 'h-2.5');
  });

  it('should render with lg size', () => {
    render(<StatusIndicator status="available" size="lg" />);
    const indicator = screen.getByTitle('在线');
    expect(indicator).toHaveClass('w-4', 'h-4');
  });

  it('should have rounded-full class', () => {
    render(<StatusIndicator status="available" />);
    const indicator = screen.getByTitle('在线');
    expect(indicator).toHaveClass('rounded-full');
  });

  it('should have white border', () => {
    render(<StatusIndicator status="available" />);
    const indicator = screen.getByTitle('在线');
    expect(indicator).toHaveClass('border-2', 'border-white');
  });

  it('should not have pulse animation for available status', () => {
    render(<StatusIndicator status="available" />);
    const indicator = screen.getByTitle('在线');
    // The component doesn't include pulse animation class
    expect(indicator).not.toHaveClass('animate-pulse');
  });

  it('should render as a div element', () => {
    render(<StatusIndicator status="available" />);
    const indicator = screen.getByTitle('在线');
    expect(indicator.tagName.toLowerCase()).toBe('div');
  });
});