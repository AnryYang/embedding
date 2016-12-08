package embedding;

import com.vividsolutions.jts.geom.Coordinate;
import com.vividsolutions.jts.geom.GeometryFactory;
import com.vividsolutions.jts.geom.Point;

import java.io.*;

/**
 * Parse taxi trip files.
 *
 * There are two types of raw taxi trips.
 *      Type 1: 2013-[month]
 *      Type 2: Chicago Verifone xxxx
 */
public class TaxiTrip {
    public enum TAXITYPE { Type1, Type2 };

    public static TAXITYPE tripFormat;
    public static final String tripFilePath = "../data/ChicagoTaxi";
    public static GeometryFactory pointsBuilder = new GeometryFactory();

    ShortDate startDate;
    ShortDate endDate;
    Point startLoc;
    Point endLoc;
    int duration;   // in seconds

    public TaxiTrip() {
        // empty
    }

    /**
     * Parse taxi trips from one input line.
     * @param line
     */
    public TaxiTrip(String line) {
        if (tripFormat ==  TAXITYPE.Type1) {
            String[] ls = line.split("\t+");
            this.startDate = new ShortDate(ls[7]);
            this.endDate = new ShortDate(ls[8]);
            this.startLoc = parseGPS(ls[9]);
            this.endLoc = parseGPS(ls[10]);
            this.duration = Integer.parseInt(ls[2]);
        } else if (tripFormat == TAXITYPE.Type2) {

        } else {
            System.err.println("Wrong trip format is given.");
        }
    }

    /**
     * Parse the gps string in type1 taxi file.
     * @param gps GPS string with format "41.9737,-87.8681", the quotations are included.
     * @return a Point object
     */
    Point parseGPS(String gps) {
        String g = gps.substring(1, gps.length()-1);
        String[] gs = g.split(",");
        Coordinate coord = new Coordinate(Double.parseDouble(gs[0]), Double.parseDouble(gs[1]));
        return pointsBuilder.createPoint(coord);
    }


    public static void parseTaxiFiles() {
        File taxiDir = new File(tripFilePath);
        String[] filesType1 = taxiDir.list(new FilenameFilter() {
            @Override
            public boolean accept(File file, String s) {
                return s.startsWith("201");
            }
        });
        tripFormat = TAXITYPE.Type1;
        try {
            for (String fn : filesType1) {
                BufferedReader fin = new BufferedReader(new FileReader(tripFilePath + File.separator + fn));
                String l = fin.readLine();  // header
                System.out.println(l);
                System.out.println(fin.readLine());
                while ((l = fin.readLine()) != null) {
                    TaxiTrip t = new TaxiTrip(l);
                    break;
                }
            }
        } catch (Exception e) {
            e.printStackTrace();
        }
    }

    public static void main(String[] args) {
        parseTaxiFiles();
    }
}


class ShortDate {
    byte month;
    byte day;
    byte hour;
    byte minute;

    public ShortDate(int m, int d, int h, int min) {
        this.month = (byte) m;
        this.day = (byte) d;
        this.hour = (byte) h;
        this.minute = (byte) min;
    }

    /**
     * Parse the date in Type1 taxi data.
     * @param s datetime string, e.g. "11/30/13 20:07", "12/1/13 2:31"
     */
    public ShortDate(String s) {
        String[] fields = s.split("[/ :]");
        this.month = Byte.parseByte(fields[0]);
        this.day = Byte.parseByte(fields[1]);
        this.hour = Byte.parseByte(fields[3]);
        this.minute = Byte.parseByte(fields[4]);
    }
}