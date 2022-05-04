//import logo from './logo.svg';
import './App.css';
import { HBox, VBox, SplitPanel, Panel } from './panel';

function App() {
  return (
    <VBox sx={{ height: '100%' }}>
        <SplitPanel direction='horizontal'>
            <Panel sx={{
                backgroundColor: 'yellow'
            }} />
            <Panel sx={{
                backgroundColor: 'lime'
            }}></Panel>
        </SplitPanel>
    </VBox>
  );
}

export default App;
