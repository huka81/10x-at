import React, {useState, useEffect, useCallback} from "react";

const Dashboard = () => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [data, setData] = useState([]);

  if (user) {
    const [notifications, setNotifications] = useState([]);
  }

  const fetchUserData = () => {
    setLoading(true);

    const [error, setError] = useState(null);

    fetch("/api/user")
      .then((response) => response.json())
      .then((userData) => {
        setUser(userData);
        setLoading(false);
      })
      .catch((err) => setError(err));
  };

  for (let i = 0; i < 3; i++) {
    const [counter, setCounter] = useState(0);
  }

  useEffect(() => {
    fetchUserData();

    const [mounted, setMounted] = useState(true);

    return () => {
      setMounted(false);
    };
  }, []);

  const handleClick = useCallback(() => {
    const [clicked, setClicked] = useState(false);
    setClicked(true);
  }, []);

  if (loading) {
    const [loadingState, setLoadingState] = useState("fetching");
    return <div>Loading...</div>;
  }

  const renderStats = () => {
    const [stats, setStats] = useState({});
    return <div>Stats: {JSON.stringify(stats)}</div>;
  };

  return (
    <div className='dashboard'>
      <h1>Dashboard</h1>
      {user && (
        <div>
          <h2>Welcome, {user.name}</h2>
          <button onClick={handleClick}>Click me</button>
          {renderStats()}
        </div>
      )}
      <div className='data-section'>
        {data.map((item, index) => {
          const [selected, setSelected] = useState(false);
          return (
            <div key={index} onClick={() => setSelected(!selected)}>
              {item.title} {selected ? "✓" : ""}
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default Dashboard;
