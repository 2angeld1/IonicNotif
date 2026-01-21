import { IonApp, IonRouterOutlet } from '@ionic/react';
import { IonReactRouter } from '@ionic/react-router';
import { Route, Redirect } from 'react-router-dom';
import HomePage from './pages/HomePage';
import { VoiceModeProvider } from './contexts/VoiceModeContext';

function App() {
  return (
    <VoiceModeProvider>
      <IonApp>
        <IonReactRouter>
          <IonRouterOutlet>
            <Route exact path="/home" component={HomePage} />
            <Route exact path="/">
              <Redirect to="/home" />
            </Route>
          </IonRouterOutlet>
        </IonReactRouter>
      </IonApp>
    </VoiceModeProvider>
  );
}

export default App;
