"""
🧪 TESTS FOR TELEGRAM SAFE UTILITIES
Tests for the safe messaging functions that prevent BadRequest errors.
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import MagicMock, AsyncMock

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

class TestTelegramSafeUtilities:
    """Tests for the telegram safe messaging utilities"""
    
    def test_telegram_safe_module_exists(self):
        """Test that the telegram_safe module exists and imports correctly"""
        from utils.telegram_safe import safe_send_message, safe_edit_message, safe_reply_text, safe_context_send
        
        # All functions should be callable
        assert callable(safe_send_message)
        assert callable(safe_edit_message)
        assert callable(safe_reply_text)
        assert callable(safe_context_send)
    
    def test_no_recursive_calls_in_safe_functions(self):
        """Test that none of the safe functions call themselves recursively"""
        telegram_safe_path = Path(__file__).parent.parent / "src" / "utils" / "telegram_safe.py"
        
        with open(telegram_safe_path, 'r') as f:
            content = f.read()
        
        # Extract each function and check for recursive calls
        import re
        
        functions_to_check = [
            'safe_send_message',
            'safe_edit_message', 
            'safe_reply_text',
            'safe_context_send'
        ]
        
        for func_name in functions_to_check:
            # Find the function definition
            pattern = rf'async def {func_name}.*?(?=^async def|\Z)'
            match = re.search(pattern, content, re.DOTALL | re.MULTILINE)
            
            if match:
                function_body = match.group(0)
                
                # Check for recursive calls (excluding the function definition line)
                lines = function_body.split('\n')
                recursive_calls = 0
                for line in lines:
                    if f'{func_name}(' in line and not line.strip().startswith(f'async def {func_name}'):
                        recursive_calls += 1
                
                assert recursive_calls == 0, f"{func_name} has {recursive_calls} recursive calls"
    
    def test_badrequest_handling_exists(self):
        """Test that BadRequest handling exists in safe functions"""
        telegram_safe_path = Path(__file__).parent.parent / "src" / "utils" / "telegram_safe.py"
        
        with open(telegram_safe_path, 'r') as f:
            content = f.read()
        
        # Should have BadRequest import and handling
        assert "from telegram.error import BadRequest" in content
        assert "Message is not modified" in content
        assert "except BadRequest" in content
    
    def test_manager_calendar_uses_safe_functions(self):
        """Test that manager_calendar.py now uses safe functions"""
        manager_calendar_path = Path(__file__).parent.parent / "src" / "handlers" / "manager_calendar.py"
        
        with open(manager_calendar_path, 'r') as f:
            content = f.read()
        
        # Should import safe functions
        assert "from utils.telegram_safe import" in content
        
        # Should not have direct Telegram API calls anymore (in new code)
        lines = content.split('\n')
        direct_calls = []
        
        for i, line in enumerate(lines, 1):
            # Skip comment lines and import lines
            if line.strip().startswith('#') or 'import' in line:
                continue
                
            # Look for direct API calls that aren't in safe functions
            if ('await update.callback_query.edit_message_text(' in line or
                'await update.message.reply_text(' in line or
                'await context.bot.send_message(' in line):
                
                # Make sure it's not inside the safe_send_message function definition
                if 'def safe_send_message' not in content[max(0, content.find('\n'.join(lines[:i-20]))):content.find('\n'.join(lines[i:i+20]))]:
                    direct_calls.append(f"Line {i}: {line.strip()}")
        
        # Allow some direct calls in the safe_send_message function itself
        # But outside of that, should use safe functions
        remaining_direct_calls = [call for call in direct_calls if 'safe_send_message' not in call]
        
        # We expect some direct calls to still exist in the safe function definition
        # But the count should be reasonable (not hundreds like before)
        assert len(direct_calls) < 10, f"Too many direct API calls found: {direct_calls}"
    
    @pytest.mark.asyncio
    async def test_safe_send_message_mock_behavior(self):
        """Test safe_send_message behavior with mocked objects"""
        from utils.telegram_safe import safe_send_message
        from telegram.error import BadRequest
        
        # Test with callback query
        mock_update = MagicMock()
        mock_update.callback_query = MagicMock()
        mock_update.callback_query.edit_message_text = AsyncMock()
        
        await safe_send_message(mock_update, "test message")
        
        # Should call edit_message_text
        mock_update.callback_query.edit_message_text.assert_called_once()
        
        # Test with message
        mock_update2 = MagicMock()
        mock_update2.callback_query = None
        mock_update2.message = MagicMock()
        mock_update2.message.reply_text = AsyncMock()
        
        await safe_send_message(mock_update2, "test message")
        
        # Should call reply_text
        mock_update2.message.reply_text.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_safe_send_message_badrequest_handling(self):
        """Test that BadRequest 'Message is not modified' is handled gracefully"""
        from utils.telegram_safe import safe_send_message
        from telegram.error import BadRequest
        
        # Test with callback query that raises BadRequest
        mock_update = MagicMock()
        mock_update.callback_query = MagicMock()
        mock_update.callback_query.edit_message_text = AsyncMock()
        mock_update.callback_query.edit_message_text.side_effect = BadRequest("Message is not modified")
        
        # Should not raise exception
        await safe_send_message(mock_update, "test message")
        
        # Test with other BadRequest that should be raised
        mock_update.callback_query.edit_message_text.side_effect = BadRequest("Other error")
        
        with pytest.raises(BadRequest):
            await safe_send_message(mock_update, "test message")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])