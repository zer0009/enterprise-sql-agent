#!/usr/bin/env python3
"""
Response Formatter Module
Handles response formatting, parsing, validation, and error handling.
"""

from typing import Dict, Any, List, Optional, Tuple
import re
import json


class ResponseFormatter:
    """Handles response formatting, parsing, validation, and error handling."""
    
    def __init__(self):
        self._validation_stats = {
            'total_responses': 0,
            'methodology_compliant': 0
        }
    
    def analyze_content(self, content: str) -> Dict[str, Any]:
        """Analyze content to determine its type and characteristics."""
        try:
            if not content or not isinstance(content, str):
                return {
                    'type': 'empty',
                    'has_data': False,
                    'has_summary': False,
                    'complexity': 'low',
                    'length': 0
                }
            
            content_lower = content.lower()
            
            # Check for data patterns
            has_tuples = '(' in content and ')' in content
            has_brackets = '[' in content and ']' in content
            has_numbers = bool(re.search(r'\d+', content))
            has_sql_keywords = any(keyword in content_lower for keyword in 
                                 ['select', 'from', 'where', 'group by', 'order by'])
            
            # Determine content type
            content_type = 'text'
            if has_tuples or has_brackets:
                content_type = 'data'
            elif 'summary' in content_lower or 'total' in content_lower:
                content_type = 'summary'
            elif len(content.split('\n')) > 5:
                content_type = 'list'
            
            # Determine complexity
            complexity = 'low'
            if len(content) > 500:
                complexity = 'high'
            elif len(content) > 200 or content.count('\n') > 3:
                complexity = 'medium'
            
            return {
                'type': content_type,
                'has_data': has_tuples or has_brackets or has_numbers,
                'has_summary': 'summary' in content_lower,
                'has_sql': has_sql_keywords,
                'complexity': complexity,
                'length': len(content),
                'line_count': content.count('\n') + 1
            }
            
        except Exception as e:
            print(f"⚠️ Content analysis failed: {e}")
            return {
                'type': 'text',
                'has_data': False,
                'has_summary': False,
                'complexity': 'low',
                'length': len(content) if content else 0
            }
    
    def analyze_validation_quality(self, content: str) -> Dict[str, Any]:
        """Analyze validation quality and provide scoring."""
        try:
            if not content:
                return {'score': 0, 'issues': ['Empty content'], 'suggestions': []}
            
            content_lower = content.lower()
            score = 0
            issues = []
            suggestions = []
            
            # Check for validation indicators
            validation_keywords = [
                'validation', 'verified', 'checked', 'confirmed',
                'quality', 'accuracy', 'completeness'
            ]
            
            if any(keyword in content_lower for keyword in validation_keywords):
                score += 30
            else:
                issues.append('No validation indicators found')
                suggestions.append('Include validation steps in your analysis')
            
            # Check for data quality mentions
            quality_keywords = [
                'duplicate', 'null', 'missing', 'invalid',
                'consistent', 'accurate', 'complete'
            ]
            
            if any(keyword in content_lower for keyword in quality_keywords):
                score += 25
            else:
                suggestions.append('Consider data quality aspects')
            
            # Check for business logic validation
            business_keywords = [
                'reasonable', 'expected', 'business rule',
                'logic', 'requirement', 'specification'
            ]
            
            if any(keyword in content_lower for keyword in business_keywords):
                score += 25
            else:
                suggestions.append('Include business logic validation')
            
            # Check for technical validation
            technical_keywords = [
                'syntax', 'schema', 'column', 'table',
                'data type', 'constraint', 'index'
            ]
            
            if any(keyword in content_lower for keyword in technical_keywords):
                score += 20
            else:
                suggestions.append('Add technical validation details')
            
            # Determine quality level
            if score >= 80:
                quality = 'high'
            elif score >= 60:
                quality = 'medium'
            else:
                quality = 'low'
            
            return {
                'score': score,
                'quality': quality,
                'issues': issues,
                'suggestions': suggestions
            }
            
        except Exception as e:
            print(f"⚠️ Validation quality analysis failed: {e}")
            return {
                'score': 0,
                'quality': 'low',
                'issues': ['Analysis failed'],
                'suggestions': ['Please try again']
            }
    
    def format_content_for_display(self, content: str, content_analysis: Dict[str, Any]) -> str:
        """Format content for display based on its type and characteristics."""
        try:
            content_type = content_analysis.get('type', 'text')
            
            if content_type == 'data':
                return self.format_data_results(content)
            elif content_type == 'list':
                return self.format_list_content(content)
            elif content_type == 'summary':
                return self.format_summary_content(content)
            else:
                return self.format_text_content(content)
                
        except Exception as e:
            print(f"⚠️ Content formatting failed: {e}")
            return content
    
    def format_data_results(self, content: str) -> str:
        """Format structured data results into a clean, table-like structure."""
        try:
            if not content:
                return "No data available"
            
            lines = content.strip().split('\n')
            formatted_lines = []
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                # Format tuple-like data
                if line.startswith('(') and line.endswith(')'):
                    # Remove parentheses and format as table row
                    data = line[1:-1]
                    # Split by comma and clean up
                    parts = [part.strip().strip("'\"") for part in data.split(',')]
                    formatted_line = " | ".join(parts)
                    formatted_lines.append(formatted_line)
                else:
                    formatted_lines.append(line)
            
            if formatted_lines:
                return "\n".join(formatted_lines)
            else:
                return content
                
        except Exception as e:
            print(f"⚠️ Data formatting failed: {e}")
            return content
    
    def format_list_content(self, content: str) -> str:
        """Format list-like content with proper bullet points."""
        try:
            lines = content.strip().split('\n')
            formatted_lines = []
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                # Add bullet points if not already present
                if not line.startswith(('•', '-', '*', '1.', '2.', '3.')):
                    line = f"• {line}"
                
                formatted_lines.append(line)
            
            return "\n".join(formatted_lines)
            
        except Exception as e:
            print(f"⚠️ List formatting failed: {e}")
            return content
    
    def format_summary_content(self, content: str) -> str:
        """Format summary content with clear structure."""
        try:
            # Add summary header if not present
            if not content.lower().startswith('summary'):
                content = f"Summary:\n{content}"
            
            return content
            
        except Exception as e:
            print(f"⚠️ Summary formatting failed: {e}")
            return content
    
    def format_text_content(self, content: str) -> str:
        """Format general text content for better readability."""
        try:
            if not content:
                return "No content available"
            
            # Clean up extra whitespace
            content = re.sub(r'\n\s*\n', '\n\n', content)
            content = content.strip()
            
            return content
            
        except Exception as e:
            print(f"⚠️ Text formatting failed: {e}")
            return content
    
    def generate_summary(self, content: str, content_analysis: Dict[str, Any], validation_quality: Dict[str, Any]) -> str:
        """Generate a summary including validation quality assessment."""
        try:
            summary_parts = []
            
            # Content summary
            if content_analysis['has_data']:
                summary_parts.append("Data results retrieved and formatted")
            else:
                summary_parts.append("Information processed successfully")
            
            # Validation quality
            quality = validation_quality.get('quality', 'unknown')
            score = validation_quality.get('score', 0)
            summary_parts.append(f"Validation Quality: {quality.title()} ({score}/100)")
            
            # Suggestions if quality is low
            if quality == 'low':
                suggestions = validation_quality.get('suggestions', [])
                if suggestions:
                    summary_parts.append(f"Improvement suggestions: {', '.join(suggestions[:2])}")
            
            return " | ".join(summary_parts)
            
        except Exception as e:
            print(f"⚠️ Summary generation failed: {e}")
            return "Summary generation failed"
    
    def generate_suggestions(self, question: str, content_analysis: Dict[str, Any], 
                           validation_quality: Dict[str, Any]) -> List[str]:
        """Generate context-specific suggestions for improvement."""
        try:
            suggestions = []
            
            # Content-based suggestions
            if content_analysis.get('type') == 'data':
                suggestions.append("Consider adding data validation checks")
                suggestions.append("Verify data completeness and accuracy")
            
            if content_analysis.get('complexity') == 'high':
                suggestions.append("Break down complex results into smaller sections")
            
            # Validation-based suggestions
            validation_suggestions = validation_quality.get('suggestions', [])
            suggestions.extend(validation_suggestions[:3])  # Limit to 3
            
            # General suggestions
            if not content_analysis.get('has_summary'):
                suggestions.append("Add a summary of key findings")
            
            return suggestions[:5]  # Limit to 5 suggestions
            
        except Exception as e:
            print(f"⚠️ Suggestion generation failed: {e}")
            return ["Please review the results for accuracy"]
    
    def suggest_ui_components(self, content_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Suggest appropriate UI components based on content analysis."""
        try:
            content_type = content_analysis.get('type', 'text')
            
            if content_type == 'data':
                return {"type": "data_table", "icon": "📊", "color": "primary"}
            elif content_type == 'list':
                return {"type": "list_view", "icon": "📋", "color": "info"}
            elif content_type == 'summary':
                return {"type": "summary_card", "icon": "📈", "color": "success"}
            else:
                return {"type": "text_message", "icon": "💬", "color": "default"}
            
        except Exception as e:
            print(f"⚠️ UI component suggestion failed: {e}")
            return {"type": "text_message", "icon": "💬", "color": "default"}
    
    def validate_agent_response_format(self, response: str) -> Tuple[bool, float, List[str]]:
        """Validate agent response against ReAct format and new validation methodology."""
        try:
            self._validation_stats['total_responses'] += 1
            
            if not response:
                return False, 0.0, ["Empty response"]
            
            response_lower = response.lower()
            issues = []
            score = 0
            
            # Check for ReAct components (40 points total)
            if 'thought:' in response_lower:
                score += 10
            else:
                issues.append("Missing 'Thought:' component")
            
            if 'action:' in response_lower:
                score += 10
            else:
                issues.append("Missing 'Action:' component")
            
            if 'observation:' in response_lower:
                score += 10
            else:
                issues.append("Missing 'Observation:' component")
            
            if 'final answer:' in response_lower:
                score += 10
            else:
                issues.append("Missing 'Final Answer:' component")
            
            # Check for new validation methodology (60 points total)
            # Schema exploration (20 points)
            schema_keywords = ['schema', 'table', 'column', 'structure']
            if any(keyword in response_lower for keyword in schema_keywords):
                score += 20
            else:
                issues.append("Missing schema exploration")
            
            # Validation checks (40 points)
            validation_keywords = [
                'validation', 'verify', 'check', 'quality',
                'duplicate', 'null', 'missing', 'accuracy'
            ]
            validation_count = sum(1 for keyword in validation_keywords 
                                 if keyword in response_lower)
            
            if validation_count >= 3:
                score += 40
            elif validation_count >= 2:
                score += 25
            elif validation_count >= 1:
                score += 15
            else:
                issues.append("Missing comprehensive validation checks")
            
            # Determine if methodology compliant (score >= 70)
            is_compliant = score >= 70
            if is_compliant:
                self._validation_stats['methodology_compliant'] += 1
            
            format_score = score / 100.0
            
            return is_compliant, format_score, issues
            
        except Exception as e:
            print(f"⚠️ Response format validation failed: {e}")
            return False, 0.0, ["Validation failed"]
    
    def parse_agent_response(self, raw_response: str) -> str:
        """Extract and format the final answer from raw agent response."""
        try:
            if not raw_response:
                return "No response received"
            
            # Look for Final Answer section
            final_answer_match = re.search(
                r'final answer:(.+?)(?=\n(?:thought:|action:|observation:)|$)',
                raw_response,
                re.IGNORECASE | re.DOTALL
            )
            
            if final_answer_match:
                final_answer = final_answer_match.group(1).strip()
                
                # Check if it contains SQL query results
                if '(' in final_answer and ')' in final_answer:
                    return self.format_sql_results(final_answer)
                else:
                    return self.clean_and_format_response(final_answer)
            
            # Fallback: look for any structured data in the response
            return self.extract_meaningful_content(raw_response)
            
        except Exception as e:
            print(f"⚠️ Response parsing failed: {e}")
            return "Failed to parse response"
    
    def clean_and_format_response(self, response: str) -> str:
        """Clean and format response for professional presentation."""
        try:
            if not response:
                return "No content to format"
            
            # Remove extra whitespace
            response = re.sub(r'\s+', ' ', response)
            response = response.strip()
            
            # Handle data-like content specially
            if ('(' in response and ')' in response) or ('[' in response and ']' in response):
                return self.format_data_results(response)
            
            # Clean up common formatting issues
            response = re.sub(r'\n\s*\n', '\n\n', response)
            
            return response
            
        except Exception as e:
            print(f"⚠️ Response cleaning failed: {e}")
            return response
    
    def format_sql_results(self, content: str, additional_content: str = None) -> str:
        """Format SQL query results for better presentation."""
        try:
            formatted_content = self.format_data_results(content)
            
            if additional_content:
                return f"{formatted_content}\n\n{additional_content}"
            
            return formatted_content
            
        except Exception as e:
            print(f"⚠️ SQL results formatting failed: {e}")
            return content
    
    def extract_meaningful_content(self, raw_output: str) -> str:
        """Extract meaningful content from raw output as fallback."""
        try:
            lines = raw_output.split('\n')
            meaningful_lines = []
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                # Skip agent artifacts
                if any(prefix in line.lower() for prefix in [
                    'thought:', 'action:', 'observation:', 'action input:',
                    'could not parse', 'llm output:', 'error:'
                ]):
                    continue
                
                # Include meaningful content
                if len(line) > 10:
                    meaningful_lines.append(line)
            
            if meaningful_lines:
                return '\n'.join(meaningful_lines)  # Return all meaningful lines
            
            return "Unable to extract meaningful content from response"
            
        except Exception as e:
            print(f"⚠️ Content extraction failed: {e}")
            return "Content extraction failed"
    
    def create_structured_response(self, content: str, processing_time: float = 0.0, 
                                 query_time: float = 0.0) -> Dict[str, Any]:
        """Create a comprehensive structured response."""
        try:
            # Analyze content
            content_analysis = self.analyze_content(content)
            validation_quality = self.analyze_validation_quality(content)
            
            # Format content
            formatted_content = self.format_content_for_display(content, content_analysis)
            
            # Validate format
            is_compliant, format_score, format_issues = self.validate_agent_response_format(content)
            
            # Generate suggestions
            suggestions = self.generate_suggestions("", content_analysis, validation_quality)
            
            # Generate summary
            summary = self.generate_summary(content, content_analysis, validation_quality)
            
            # Suggest UI components
            ui_components = self.suggest_ui_components(content_analysis)
            
            return {
                'status': 'success',
                'content': formatted_content,
                'summary': summary,
                'metadata': {
                    'processing_time': processing_time,
                    'query_time': query_time,
                    'content_type': content_analysis['type'],
                    'has_data': content_analysis['has_data'],
                    'record_count': content_analysis.get('record_count', 0),
                    'validation_quality': validation_quality,
                    'timestamp': None  # Will be set by caller
                },
                'performance': {
                    'processing_time': processing_time,
                    'query_time': query_time
                },
                'validation': {
                    'format_score': format_score,
                    'methodology_compliant': is_compliant,
                    'quality_score': validation_quality.get('score', 0),
                    'issues': format_issues
                },
                'suggestions': suggestions,
                'ui_components': ui_components
            }
            
        except Exception as e:
            print(f"⚠️ Structured response creation failed: {e}")
            return {
                'status': 'error',
                'content': f"Response formatting failed: {str(e)}",
                'summary': "Error occurred during response formatting",
                'metadata': {
                    'processing_time': processing_time,
                    'query_time': query_time,
                    'content_type': 'error',
                    'has_data': False,
                    'record_count': 0,
                    'validation_quality': {'score': 0, 'issues': ['Formatting failed']},
                    'timestamp': None
                },
                'performance': {
                    'processing_time': processing_time,
                    'query_time': query_time
                },
                'validation': {
                    'format_score': 0.0,
                    'methodology_compliant': False,
                    'quality_score': 0,
                    'issues': ['Formatting failed']
                },
                'suggestions': ['Please try rephrasing your question'],
                'ui_components': {'type': 'error_message', 'icon': '⚠️', 'color': 'error'}
            }
    
    def extract_from_intermediate_steps(self, intermediate_steps) -> str:
        """Extract useful information from intermediate steps when agent fails."""
        try:
            if not intermediate_steps:
                return None
            
            sql_results = []
            observations = []
            
            for step in intermediate_steps:
                if isinstance(step, tuple) and len(step) >= 2:
                    action, observation = step[0], step[1]
                    
                    if observation and isinstance(observation, str):
                        obs_lines = observation.split('\n')
                        for line in obs_lines:
                            line = line.strip()
                            if (line.startswith('(') and line.endswith(')')) or \
                               (line.startswith('[') and line.endswith(']')):
                                sql_results.append(line)
                            elif len(line) > 20 and not any(skip in line.lower() for skip in 
                                ['error', 'failed', 'could not']):
                                observations.append(line)
            
            response_parts = []
            
            if sql_results:
                response_parts.append("Based on the query execution, here are the results:")
                response_parts.extend(sql_results[:10])
            
            if observations:
                response_parts.append("\nAdditional information:")
                response_parts.extend(observations[:3])
            
            if response_parts:
                return "\n".join(response_parts)
            
            return None
            
        except Exception as e:
            return None
    
    def get_validation_stats(self) -> Dict[str, Any]:
        """Get validation statistics."""
        total = self._validation_stats['total_responses']
        compliant = self._validation_stats['methodology_compliant']
        
        compliance_rate = (compliant / total * 100) if total > 0 else 0
        
        return {
            'total_responses': total,
            'methodology_compliant': compliant,
            'compliance_rate': compliance_rate
        }


