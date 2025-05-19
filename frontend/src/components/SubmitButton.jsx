
import axios from 'axios';

const SubmitButton = ({ code, language, setOutput, setError }) => {
  const handleSubmit = async () => {
    try {
      const res = await axios.post("http://localhost:8000/api/run_code/", {
        code,
        language
      });
      console.log("Backend response:", res.data);

      setOutput(res.data.stdout);
      setError(res.data.stderr);
    } catch (err) {
      console.error("Error executing code:", err);
      setError("An error occurred while executing the code.");
    }
  };

  return (
    <button style={styles.button} onClick={handleSubmit}>
      Run Code
    </button>
  );
};

const styles = {
  button: {
    padding: '8px 16px',
    fontSize: '1rem',
    cursor: 'pointer',
    backgroundColor: '#4CAF50',
    color: '#fff',
    border: 'none',
    borderRadius: '4px',
  },
};

export default SubmitButton;

