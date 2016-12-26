package embedding;

import com.vividsolutions.jts.geom.MultiPolygon;
import junit.framework.TestCase;
import org.geotools.data.simple.SimpleFeatureIterator;
import org.opengis.feature.simple.SimpleFeature;

import java.io.File;
import java.io.IOException;
import java.util.LinkedList;
import java.util.List;

/**
 * Unit test for Tracts class.
 */
public class TractsTest extends TestCase {

    public void testShapeFileExists() {
        File f = new File(Tracts.shapeFilePath);
        assertTrue(f.exists());
    }

    public void testAllShapesArePolygon() {
        try {
            SimpleFeatureIterator features = Tracts.getShapeFileFeatures();
            SimpleFeature shp = features.next();

            int fieldSize = shp.getType().getTypes().size();
            assertEquals(fieldSize, 10);
            assertEquals(shp.getType().getType(3).getName().getLocalPart(), "tractce10");
            assertEquals(shp.getType().getType(0).getName().getLocalPart(), "MultiPolygon");
            for (int i = 0; i < fieldSize; i++){
                System.out.println(shp.getType().getType(i).getName().getLocalPart());
            }

            int cnt = 1;
            while (features.hasNext()) {
                shp = features.next();
                MultiPolygon g = (MultiPolygon) shp.getDefaultGeometry();
                cnt ++;
            }
            assertEquals(cnt, 801);
            features.close();
            Tracts.shapefile.dispose();
        } catch (IOException e) {
            e.printStackTrace();
        }
    }

    public void testSortedIDs() {
        Tracts trts = new Tracts();
        List<Integer> sortedIds = new LinkedList<>(trts.tracts.keySet());
        sortedIds.sort((a, b) -> a.compareTo(b));
        assertEquals(sortedIds.size(), 801);
        assertEquals((int) sortedIds.get(0), 10100);
        assertEquals((int) sortedIds.get(800), 980100);
        assertTrue(sortedIds.get(0) < sortedIds.get(800));
    }

}